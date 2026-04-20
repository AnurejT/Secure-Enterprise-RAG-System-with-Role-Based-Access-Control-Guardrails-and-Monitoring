# services/rag_service.py

from rag.retriever import get_relevant_docs
from rag.llm import get_llm_response
from rbac.access_control import filter_docs_by_role


# 🔥 Query Rewriting
def rewrite_query(query):
    prompt = f"""
Convert the question into a factual search query.

Examples:
"Can audits be skipped?" → audit mandatory financial compliance
"Can salary be processed before the 1st?" → salary processing policy date
"Can expenses be reimbursed without receipts?" → expense reimbursement receipt requirement

Query: {query}
Rewritten:
"""
    result = get_llm_response(prompt)
    rewritten = result["content"].strip()

    print("\n[RAG] Rewritten Query:", rewritten)

    return rewritten


def process_query(user_query, role="employee"):
    print("\n==============================")
    print("[RAG] USER QUERY:", user_query)
    print("[RAG] ROLE:", role)
    print("==============================")

    # 🔥 STEP 1: Rewrite query
    rewritten_query = rewrite_query(user_query)

    # 🔥 STEP 2: Hybrid retrieval
    docs1 = get_relevant_docs(user_query)
    docs2 = get_relevant_docs(rewritten_query)

    docs = docs1 + docs2

    if not docs:
        return {
            "answer": "No information available.",
            "sources": []
        }

    # 🔐 STEP 3: RBAC
    docs = filter_docs_by_role(docs, role)

    if not docs:
        return {
            "answer": "No information available for your role.",
            "sources": []
        }

    print(f"\n[RBAC] Doc count after filter: {len(docs)}")

    # 🔥 STEP 4: Remove duplicates
    seen = set()
    unique_docs = []

    for d in docs:
        text = d.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_docs.append(d)

    docs = unique_docs

    # 🔥 STEP 5: Context
    context = "\n\n".join([d.page_content for d in docs])

    print("\n[RAG] FINAL CONTEXT:\n")
    print(context[:1000])

    # FINAL PROMPT — strictly grounded, no hallucination
    prompt = f"""You are a secure enterprise AI assistant.

RULES (follow strictly):
1. Answer ONLY from the context provided below.
2. Do NOT use any outside knowledge or make assumptions.
3. Do NOT infer, guess, or fabricate information not explicitly stated.
4. If the context does not contain the answer, respond with exactly:
   "No information available in the documents accessible to your role."
5. Do NOT explain what you cannot do. Just answer or say the phrase above.

Context:
{context}

Question: {user_query}

Answer:"""

    llm_result = get_llm_response(prompt)

    answer = llm_result["content"]

    print("\n[RAG] ANSWER:\n", answer)

    return {
        "answer": answer,
        "sources": [d.metadata for d in docs]
    }