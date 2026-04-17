# services/rag_service.py

from rag.retriever import get_relevant_docs
from rbac.access_control import rbac_filter
from rag.llm import get_llm_response

from guardrails.filters import (
    is_malicious_query,
    is_irrelevant_query,
    check_empty_context,
    enforce_output_constraints
)

import time

# ⏱️ Simple rate limiting
last_query_time = 0


def rate_limit():
    global last_query_time
    current_time = time.time()

    if current_time - last_query_time < 2:
        return False

    last_query_time = current_time
    return True


def process_query(query, user_role):

    # ---------------- INPUT GUARDRAILS ---------------- #

    if not rate_limit():
        return "⚠️ Too many requests. Please wait."

    if is_malicious_query(query):
        return "❌ Query blocked due to sensitive content"

    if is_irrelevant_query(query):
        return "❌ Query not relevant to enterprise data"

    if len(query) > 300:
        return "❌ Query too long"

    # ---------------- RETRIEVAL ---------------- #

    docs = get_relevant_docs(query)
    print(f"[RAG] Retrieved {len(docs)} docs")

    # ---------------- RBAC ---------------- #

    docs = rbac_filter(docs, user_role)
    print(f"[RBAC] After filter: {len(docs)} docs")

    # ---------------- CONTEXT GUARDRAIL ---------------- #

    if check_empty_context(docs):
        return "No information available"

    # ---------------- PREPARE CONTEXT ---------------- #

    context = "\n".join([doc.page_content for doc in docs])

    # ---------------- LLM ---------------- #

    prompt = f"""
You are a secure enterprise assistant.

Rules:
- Answer ONLY from the given context
- Do NOT make assumptions
- If answer is not found, say: "No information available"

Context:
{context}

Question:
{query}

Answer:
"""

    response = get_llm_response(prompt)
    answer = response

    # ---------------- OUTPUT GUARDRAILS ---------------- #

    answer = enforce_output_constraints(answer)

    return answer