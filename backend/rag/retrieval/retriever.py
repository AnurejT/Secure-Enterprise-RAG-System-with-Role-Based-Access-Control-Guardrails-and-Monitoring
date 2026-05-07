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
    1. Broad vector search (top-50)
    2. RBAC filter
    3. Optional employee_id filter
    4. Hybrid ranking (keyword score)
    5. Return top-10
    """
    embeddings = get_embeddings()

    print(f"\n[Retriever] query='{query[:60]}' role='{role}'")

    # ── 1. Broad fetch ────────────────────────────────────────────
    fetch_k  = 200 if employee_id else 100
    raw_docs = vector_repo.similarity_search(query, embeddings, k=fetch_k)

    # ── 2. RBAC filter ────────────────────────────────────────────
    allowed = filter_by_role(raw_docs, role)
    if not allowed:
        print("[Retriever] No documents permitted for this role.")
        return []

    # ── 3. Employee filter (optional) ────────────────────────────
    if employee_id:
        emp_filtered = [
            d for d in allowed
            if d.metadata.get("employee_id") == employee_id
        ]
        print(f"[Retriever] Employee filter: {len(emp_filtered)}/{len(allowed)}")
        if emp_filtered:
            allowed = emp_filtered

    # ── 4. Hybrid ranking ─────────────────────────────────────────
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
