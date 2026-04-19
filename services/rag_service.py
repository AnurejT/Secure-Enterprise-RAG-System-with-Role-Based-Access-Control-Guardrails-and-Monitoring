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
    if role.lower() == "admin":
        # Admin has full unrestricted access across all departments
        prompt = f"""
You are an enterprise AI assistant with full administrative access to all departments.

RULES:
- Answer using the provided context from any department.
- Be comprehensive and accurate.
- If the answer is not in the context, say "No information available."
- Do NOT guess or hallucinate.

CONTEXT (all departments):
{context}

QUESTION: {user_query}

ANSWER:
"""
    else:
        # Non-admin: strictly scoped to their department only
        prompt = f"""
You are a secure enterprise AI assistant with strict role-based access control.

STRICT RULES:
- Answer ONLY using the provided context below.
- The user's role is: {role.upper()}. Only answer questions relevant to this role/department.
- If the context contains information from a DIFFERENT department, IGNORE it and say "No information available for your role."
- Do NOT guess, hallucinate, or use general knowledge outside the context.
- Do NOT reveal information from other departments.

ROLE: {role}

CONTEXT (filtered to {role} department):
{context}

QUESTION: {user_query}

ANSWER (strictly from {role} context only):
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