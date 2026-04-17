from rag.retriever import get_relevant_docs
from rag.llm import get_llm_response
from rbac.access_control import filter_docs_by_role
from guardrails.filters import input_guardrail


def process_query(user_query, role="employee"):
    """
    Main RAG pipeline service:
    Retriever → RBAC → Guardrails → LLM
    """

    # ---------------------------
    # 1. INPUT GUARDRAIL
    # ---------------------------
    if not input_guardrail(user_query):
        return {
            "answer": "Request blocked by security guardrails.",
            "sources": []
        }

    # ---------------------------
    # 2. RETRIEVE DOCUMENTS
    # ---------------------------
    docs = get_relevant_docs(user_query)

    if not docs:
        return {
            "answer": "No information available",
            "sources": []
        }

    # ---------------------------
    # 3. RBAC FILTER (IMPORTANT FIX)
    # ---------------------------
    docs = filter_docs_by_role(docs, role)

    if not docs:
        return {
            "answer": "You do not have access to this information.",
            "sources": []
        }

    # ---------------------------
    # 4. FORMAT CONTEXT SAFELY
    # ---------------------------
    context = "\n\n".join(
        [
            getattr(doc, "page_content", str(doc))
            for doc in docs
        ]
    )

    # ---------------------------
    # 5. BUILD PROMPT
    # ---------------------------
    prompt = f"""
You are an enterprise AI assistant.

STRICT RULES:
- Answer ONLY using the provided context
- If answer is not in context, say "No information available"
- Do NOT guess or hallucinate

ROLE: {role}

CONTEXT:
{context}

QUESTION:
{user_query}

FINAL ANSWER:
"""

    # ---------------------------
    # 6. GENERATE RESPONSE
    # ---------------------------
    answer = get_llm_response(prompt)

    # ---------------------------
    # 7. RETURN RESPONSE
    # ---------------------------
    return {
        "answer": answer,
        "sources": [
            getattr(doc, "metadata", {}) for doc in docs
        ]
    }