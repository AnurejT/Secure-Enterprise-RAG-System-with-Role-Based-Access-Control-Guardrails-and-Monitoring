"""
backend/rag/llm/groq_client.py
Groq / LangChain LLM client — standard invoke + streaming.
"""
import time

from langchain_groq import ChatGroq

from backend.core import config
from backend.monitoring import repository as metrics_repo


def _get_llm() -> ChatGroq:
    return ChatGroq(
        temperature=0,
        model=config.GROQ_MODEL,
        groq_api_key=config.GROQ_API_KEY,
    )


def invoke(prompt: str, role: str = "unknown", query: str = "") -> dict:
    """
    Call the LLM synchronously.
    Returns {"content": str, "usage": dict, "latency_ms": float}.
    """
    llm = _get_llm()
    try:
        t0 = time.time()
        response = llm.invoke(prompt)
        latency_ms = round((time.time() - t0) * 1000, 1)

        meta  = getattr(response, "response_metadata", {})
        raw   = meta.get("token_usage") or meta.get("usage") or {}
        usage = {
            "prompt_tokens":     raw.get("prompt_tokens",     0),
            "completion_tokens": raw.get("completion_tokens", 0),
            "total_tokens":      raw.get("total_tokens",      0),
        }

        metrics_repo.record_token_usage(usage, role=role, query_preview=query)

        return {
            "content":    response.content.strip(),
            "usage":      usage,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {"content": f"Error: {e}", "usage": {}, "latency_ms": 0}


def stream(prompt: str, role: str = "unknown", query: str = ""):
    """
    Generator that yields text chunks from the LLM stream.
    """
    llm = _get_llm()
    t0 = time.time()
    try:
        for chunk in llm.stream(prompt):
            yield chunk.content

        latency_ms = round((time.time() - t0) * 1000, 1)
        metrics_repo.record_token_usage(
            {"total_tokens": 100}, role=role, query_preview=query
        )
    except Exception as e:
        yield f"\n[LLM Stream Error]: {e}"
