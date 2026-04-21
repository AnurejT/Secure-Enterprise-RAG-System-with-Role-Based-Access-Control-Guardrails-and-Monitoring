# services/rag_service.py

from rag.retriever import get_relevant_docs
from rag.llm import get_llm_response
from rbac.access_control import filter_docs_by_role


# ─── QUERY CLASSIFIER (RULE-BASED) ─────────────
def classify_query_role(query):
    q = query.lower()

    if any(w in q for w in ["$", "spend", "budget", "expense", "payment", "approval"]):
        return "finance"

    if any(w in q for w in ["salary", "employee", "leave"]):
        return "hr"

    if any(w in q for w in ["ads", "campaign", "marketing"]):
        return "marketing"

    if any(w in q for w in ["system", "software"]):
        return "engineering"

    return "general"


# ─── QUERY REWRITE ───────────────────────────
def rewrite_query(query):
    prompt = f"""
Convert this question into search keywords.

Example:
"Can a department spend more than $5000?"
→ finance expense approval limit 5000 policy

Query:
{query}

Answer:
"""
    result = get_llm_response(prompt)
    rewritten = result["content"].strip()

    print("[REWRITE]:", rewritten)

    return rewritten


# ─── MAIN PIPELINE ───────────────────────────
def process_query(user_query, role="employee"):

    print("\n==============================")
    print("[QUERY]:", user_query)
    print("[USER ROLE]:", role)
    print("==============================")

    # 1️⃣ Rewrite query
    rewritten_query = rewrite_query(user_query)

    # 2️⃣ Retrieve documents
    docs1 = get_relevant_docs(user_query)
    docs2 = get_relevant_docs(rewritten_query)

    docs = docs1 + docs2

    if not docs:
        return {
            "answer": "No information available in the documents accessible to your role.",
            "sources": []
        }

    # DEBUG BEFORE RBAC
    print("\n[BEFORE RBAC]")
    for d in docs[:5]:
        print(d.page_content[:100])
        print("DEPT:", d.metadata.get("department"))

    # 3️⃣ RBAC FILTER
    docs = filter_docs_by_role(docs, role)

    if not docs:
        return {
            "answer": "No information available in the documents accessible to your role.",
            "sources": []
        }

    # DEBUG AFTER RBAC
    print("\n[AFTER RBAC]")
    for d in docs[:5]:
        print(d.page_content[:100])
        print("DEPT:", d.metadata.get("department"))

    # 4️⃣ Remove duplicates
    seen = set()
    unique_docs = []

    for d in docs:
        text = d.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_docs.append(d)

    docs = unique_docs[:5]

    # 5️⃣ Context
    context = "\n\n".join([d.page_content for d in docs])

    print("\n[FINAL CONTEXT]\n", context[:800])

    # 6️⃣ LLM Answer
    prompt = f"""
You are a secure enterprise AI assistant.

RULES:
- Answer ONLY from context
- Do NOT assume anything
- If not found, reply EXACTLY:
"No information available in the documents accessible to your role."

Context:
{context}

Question:
{user_query}

Answer:
"""

    result = get_llm_response(prompt)
    answer = result["content"].strip()

    if "no information" in answer.lower():
        answer = "No information available in the documents accessible to your role."

    return {
        "answer": answer,
        "sources": [d.metadata for d in docs]
    }