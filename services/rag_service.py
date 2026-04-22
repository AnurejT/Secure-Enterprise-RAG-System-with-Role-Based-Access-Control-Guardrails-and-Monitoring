# services/rag_service.py
import json
from rag.retriever import get_relevant_docs
from rag.llm import get_llm_response, get_llm_stream
from guardrails.filters import validate_input, validate_output


def process_query(user_query, role="employee"):
    print("\n==============================")
    print("[QUERY]:", user_query)
    print("[USER ROLE]:", role)
    print("==============================")

    # 1. Input Guardrails
    is_valid, message = validate_input(user_query)
    if not is_valid:
        return {"answer": message, "sources": []}

    # 2. Retrieval
    docs = get_relevant_docs(user_query, role)
    if not docs:
        return {
            "answer": "No information available in the documents accessible to your role.",
            "sources": []
        }

    # 3. Context Building
    context = "\n\n---\n\n".join([d.page_content.strip() for d in docs])

    # 4. Prompt
    prompt = f"""
You are a professional enterprise AI assistant. 
Your goal is to provide simple, clear, and attractive answers based ONLY on the provided context.

GUIDELINES:
- Use plain text only. 
- DO NOT use any Markdown formatting like '**', '###', or '__'. 
- Use simple bullet points (-) for lists.
- Be concise. Use short sentences.
- If information is missing, state it clearly.

CONTEXT:
{context}

QUESTION:
{user_query}

FINAL ANSWER (Plain Text):
"""

    # 5. LLM Call
    result = get_llm_response(prompt, role=role, query=user_query)
    answer = result.get("content", "").strip()

    # Post-process to ensure no stray asterisks
    answer = answer.replace("**", "")

    # 6. Output Guardrails
    answer = validate_output(answer, context)

    # 7. Source Cleaning
    sources = []
    for d in docs:
        sources.append({
            "source": d.metadata.get("source"),
            "page": d.metadata.get("page", 0) + 1,
            "role_allowed": d.metadata.get("role_allowed")
        })

    return {"answer": answer, "sources": sources}


def process_query_stream(user_query, role="employee"):
    """
    Generator that yields chunks of the bot's response.
    Final yield is SOURCES_JSON: followed by JSON sources.
    """
    # 1. Input Guardrails
    is_valid, message = validate_input(user_query)
    if not is_valid:
        yield f"[Guardrail]: {message}"
        return

    # 2. Retrieval
    docs = get_relevant_docs(user_query, role)
    if not docs:
        yield "No information available in the documents accessible to your role."
        return

    # 3. Context Building
    context = "\n\n---\n\n".join([d.page_content.strip() for d in docs])

    # 4. Prompt
    prompt = f"""
You are a professional enterprise AI assistant. 
Your goal is to provide simple, clear, and attractive answers based ONLY on the provided context.

GUIDELINES:
- Use plain text only. 
- DO NOT use any Markdown formatting like '**', '###', or '__'. 
- Use simple bullet points (-) for lists.
- Be concise. Use short sentences.
- If information is missing, state it clearly.

CONTEXT:
{context}

QUESTION:
{user_query}

FINAL ANSWER (Plain Text):
"""

    # 5. Stream LLM
    for chunk in get_llm_stream(prompt, role=role, query=user_query):
        # Clean chunks of any stray bolding characters as they stream
        clean_chunk = chunk.replace("**", "")
        yield clean_chunk

    # 6. Final Sources Yield
    sources = []
    for d in docs:
        sources.append({
            "source": d.metadata.get("source"),
            "page": d.metadata.get("page", 0) + 1,
            "role_allowed": d.metadata.get("role_allowed")
        })
    
    yield f"\n\nSOURCES_JSON:{json.dumps(sources)}"