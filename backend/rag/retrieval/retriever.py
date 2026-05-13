"""
backend/rag/retrieval/retriever.py
Hybrid retrieval = vector similarity + keyword scoring + RBAC filtering.
Moved from rag/retriever.py; RBAC now delegates to rbac.enforcement.
"""
import re
import os

from backend.rag.embeddings.encoder import get_embeddings
from backend.repositories import vector_repo
from backend.rbac.enforcement import filter_by_role


def _keyword_score(query: str, text: str) -> float:
    query_words = [w.lower() for w in re.findall(r"\w+", query)]
    text_lower = text.lower()
    
    score = 0.0
    for word in query_words:
        if word in text_lower:
            score += 1.0
            
    # Bonus for phrase matches
    if query.lower() in text_lower:
        score += 5.0
    
    # Bonus for department matches if department is in query
    dept_match = re.search(r"(technology|finance|hr|marketing|sales|operations|data|compliance|risk|product|design|quality assurance|business)", query, re.I)
    if dept_match:
        dept = dept_match.group(1).lower()
        # Look for "department: <dept>" or just "<dept>" in the text
        if f"department: {dept}" in text_lower:
            score += 10.0
        elif dept in text_lower:
            score += 2.0
            
    # Bonus for causal keywords if it's a "why" question
    if "why" in query.lower() or "reason" in query.lower() or "driver" in query.lower():
        # Differentiate between "HR costs" and "Business Performance"
        is_performance_query = any(k in query.lower() for k in ["profit", "revenue", "margin", "growth", "income", "net"])
        
        causal_keywords = ["cost", "expense", "driver", "because", "due to", "result", "factor", "increase", "decrease", "growth", "margin", "profit", "income", "revenue"]
        for ck in causal_keywords:
            if ck in text_lower:
                # If it's a performance query, only give large bonus to performance keywords
                if is_performance_query and ck in ["profit", "revenue", "margin", "growth", "income"]:
                    score += 15.0
                else:
                    score += 5.0 # Reduced from 10.0 to avoid overwhelming other signals

    return score


def get_relevant_docs(query: str, role: str, employee_id: str | None = None) -> list:
    """
    1. Construct RBAC filter (Pre-Filtering)
    2. Vector search with filter
    3. Hybrid ranking (keyword score)
    4. Return top-10
    """
    embeddings = get_embeddings()
    role = role.lower()

    print(f"\n[Retriever] query='{query[:60]}' role='{role}'")

    # ── 1. Construct Filter ───────────────────────────────────────
    # If admin, no filter (see everything). 
    # Otherwise, see docs for your role OR 'general' docs.
    filter_dict = None
    if role != "admin":
        # Qdrant with LangChain handles complex filters better via the native client,
        # but here we pass a simple dict that we'll convert to a 'should' (OR) filter.
        # However, our current repo helper only supports 'must' (AND).
        # Let's update the repo helper or handle the 'OR' logic here.
        # Actually, let's keep it simple: most docs are either 'general' or specific.
        pass

    # Re-importing models for complex OR filter
    # pyrefly: ignore [missing-import]
    from qdrant_client.http import models
    
    q_filter = None
    if role != "admin":
        conditions = [
            models.FieldCondition(key="metadata.role_allowed", match=models.MatchValue(value=role)),
            models.FieldCondition(key="metadata.role_allowed", match=models.MatchValue(value="general"))
        ]
        if employee_id:
            # If employee_id is provided, we MUST match it AND (role OR general)
            rbac_filter = models.Filter(should=conditions)
            emp_filter  = models.FieldCondition(key="metadata.employee_id", match=models.MatchValue(value=employee_id))
            q_filter    = models.Filter(must=[emp_filter, rbac_filter])
        else:
            q_filter = models.Filter(should=conditions)

    # ── 2. Vector Fetch (Pre-Filtered) ────────────────────────────
    # pyrefly: ignore [missing-import]
    from langchain_qdrant import QdrantVectorStore
    from backend.repositories.vector_repo import _load_or_create
    
    db = _load_or_create(embeddings)
    fetch_k = 20
    
    # We use the db directly to pass the q_filter object
    allowed = db.similarity_search(query, k=fetch_k, filter=q_filter)
    
    if not allowed:
        print("[Retriever] No documents permitted/found for this role.")
        return []

    print(f"[Retriever] RBAC Pre-filter: {len(allowed)} docs retrieved.")

    # ── 3. Hybrid ranking ─────────────────────────────────────────
    scored = sorted(
        [((_keyword_score(query, d.page_content)), d) for d in allowed],
        key=lambda x: x[0],
        reverse=True,
    )

    # Source-based expansion: If a source is in the top-1, include all its chunks from the 'allowed' pool
    top_source = scored[0][1].metadata.get("source") if scored else None
    is_summary = top_source and "summary" in top_source.lower()
        
    expanded = []
    seen_content = set()
    for _, d in scored:
        src = d.metadata.get("source")
        # If it's a summary, we are VERY restrictive to avoid cross-pollination
        if src == top_source:
            if len(expanded) < 15:
                content_hash = d.page_content[:100]
                if content_hash not in seen_content:
                    expanded.append(d)
                    seen_content.add(content_hash)
        elif not is_summary and len(expanded) < 5:
            # Only allow other sources if the primary is NOT a summary
            content_hash = d.page_content[:100]
            if content_hash not in seen_content:
                expanded.append(d)
                seen_content.add(content_hash)
    
    return expanded
