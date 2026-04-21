# rag/retriever.py

from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings


def get_relevant_docs(query):
    embeddings = get_embeddings()
    vector_db = load_vector_store(embeddings)

    print("\n[RETRIEVER] ORIGINAL QUERY:", query)

    # ─── STEP 1: Semantic Search ───────────────────────────────
    docs = vector_db.similarity_search(query, k=15)

    # ─── STEP 2: Keyword Boost (IMPROVED) ───────────────────
    keyword_docs = []

    keywords_map = {

        # Finance / Compliance
        "audit": ["audit", "financial audit", "compliance audit"],
        "finance": ["finance", "financial policy", "budget"],
        
        # Salary / Payroll
        "salary": ["salary", "payroll", "salary processing", "wages"],
        
        # Expense / Reimbursement
        "expense": ["expense", "reimbursement", "expense policy", "5000", "$5,000"],
        
        # 🔥 NEW: Budget / Spending / Approval (FIXED ISSUE)
        "budget": ["budget", "budget approval", "spending limit"],
        "spend": ["spend", "spending", "expenditure", "cost"],
        "approval": ["approval", "authorization", "manager approval", "finance approval"],
        "limit": ["limit", "threshold", "maximum amount", "5000", "$5000"],
        
        # HR
        "leave": ["leave", "leave policy", "vacation", "sick leave"],
        "employee": ["employee", "staff", "employment"],
        
        # Marketing
        "marketing": ["marketing", "campaign", "advertising", "branding"],
        
        # General policies
        "policy": ["policy", "rules", "guidelines", "procedure"]
    }

    query_lower = query.lower()

    for key, variations in keywords_map.items():
        # Trigger booster if the main key OR any specific variation is found in the query
        if key in query_lower or any(v in query_lower for v in variations):
            print(f"[RETRIEVER] Keyword match: {key}")

            for term in variations:
                extra_docs = vector_db.similarity_search(term, k=3)
                keyword_docs.extend(extra_docs)

    # ─── STEP 3: Combine Results ───────────────────────────────
    docs.extend(keyword_docs)

    # ─── STEP 4: Remove Duplicates ─────────────────────────────
    seen = set()
    unique_docs = []

    for d in docs:
        text = d.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_docs.append(d)

    docs = unique_docs

    # ─── STEP 5: Debug Retrieved Content ───────────────────────
    print("\n[RETRIEVER] FINAL RETRIEVED DOCUMENTS:\n")

    for i, d in enumerate(docs[:10]):  # show top 10
        print(f"\n--- Document {i+1} ---")
        print(d.page_content[:300])
        print("Metadata:", d.metadata)

    print(f"\n[RETRIEVER] Total unique docs retrieved: {len(docs)}")

    return docs