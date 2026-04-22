# rag/retriever.py

from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings
from collections import defaultdict
import re


# -------------------------
# SIMPLE KEYWORD SCORING
# -------------------------
def keyword_score(query, text):
    query_words = set(re.findall(r"\w+", query.lower()))
    text_words = set(re.findall(r"\w+", text.lower()))

    # overlap score
    return len(query_words & text_words)


# -------------------------
# HYBRID RETRIEVER
# -------------------------
def get_relevant_docs(query, role):
    embeddings = get_embeddings()
    vector_db = load_vector_store(embeddings)

    print("\n[HYBRID RETRIEVER]")
    print("QUERY:", query)
    print("ROLE:", role)

    # -------------------------
    # 1. FETCH DOCUMENTS
    # -------------------------
    # Fetch a wider net of documents, then filter in memory to avoid ChromaDB list-filter syntax issues.
    raw_docs = vector_db.similarity_search(query, k=20)

    # -------------------------
    # 2. STRICT RBAC FILTERING
    # -------------------------
    allowed_docs = []
    for d in raw_docs:
        roles = d.metadata.get("role_allowed", [])
        # Normalization just in case older docs stored string instead of list
        if isinstance(roles, str):
            roles = [roles]
        
        # Enforce RBAC (Admins see everything)
        if role.lower() == "admin" or role.lower() in roles or "admin" in roles:
            allowed_docs.append(d)

    # -------------------------
    # 3. HYBRID RANKING (Semantic + Keyword)
    # -------------------------
    keyword_docs = []
    for d in allowed_docs:
        score = keyword_score(query, d.page_content)
        if score > 0:
            keyword_docs.append((d, score))
            
    # Sort keyword matches
    keyword_docs = sorted(keyword_docs, key=lambda x: x[1], reverse=True)
    keyword_ranked = [d[0] for d in keyword_docs]

    # Combine ensuring no duplicates
    combined = []
    seen = set()

    for d in allowed_docs + keyword_ranked:
        content = d.page_content[:100]
        if content not in seen:
            combined.append(d)
            seen.add(content)

    # -------------------------
    # 4. FINAL TOP-K
    # -------------------------
    final_docs = combined[:5]

    print(f"\n[RESULT] Final docs: {len(final_docs)}")

    for i, d in enumerate(final_docs):
        print(f"\n--- Doc {i+1} ---")
        safe_preview = d.page_content[:150].encode('cp1252', errors='replace').decode('cp1252')
        print(safe_preview)
        print("Metadata:", d.metadata)

    return final_docs