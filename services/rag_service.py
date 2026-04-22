# services/rag_service.py

from rag.retriever import get_relevant_docs
from rag.llm import get_llm_response
from guardrails.filters import validate_input, validate_output


def process_query(user_query, role="employee"):
    print("\n==============================")
    print("[QUERY]:", user_query)
    print("[USER ROLE]:", role)
    print("==============================")

    # -------------------------
    # 🛡️ INPUT GUARDRAILS
    # -------------------------
    is_valid, message = validate_input(user_query)

    if not is_valid:
        return {
            "answer": message,
            "sources": []
        }

    # -------------------------
    # 🔍 RETRIEVAL
    # -------------------------
    docs = get_relevant_docs(user_query, role)

    if not docs:
        return {
            "answer": "No information available in the documents accessible to your role.",
            "sources": []
        }

    # -------------------------
    # 📄 CONTEXT BUILDING
    # -------------------------
    context_chunks = []
    for d in docs:
        context_chunks.append(d.page_content.strip())

    context = "\n\n---\n\n".join(context_chunks)

    # -------------------------
    # 🧠 STRONG PROMPT (ANTI-HALLUCINATION)
    # -------------------------
    prompt = f"""
You are a STRICT enterprise AI assistant.

You MUST follow these rules:

1. Answer ONLY using the provided context
2. DO NOT use prior knowledge
3. DO NOT guess or infer
4. If the answer is not explicitly present, respond EXACTLY:
"No information available in the documents accessible to your role."
5. Keep answer concise and factual

---------------------
CONTEXT:
{context}
---------------------

QUESTION:
{user_query}

FINAL ANSWER:
"""

    # -------------------------
    # 🤖 LLM CALL
    # -------------------------
    result = get_llm_response(prompt, role=role, query=user_query)

    answer = result.get("content", "").strip()

    # -------------------------
    # 🛡️ OUTPUT GUARDRAILS
    # -------------------------
    answer = validate_output(answer, context)

    # -------------------------
    # 📊 SOURCE CLEANING
    # -------------------------
    sources = []
    for d in docs:
        sources.append({
            "source": d.metadata.get("source"),
            "role_allowed": d.metadata.get("role_allowed")
        })

    return {
        "answer": answer,
        "sources": sources
    }