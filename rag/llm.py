import os
import time
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from monitoring import token_tracker

load_dotenv()


def get_llm():
    return ChatGroq(
        temperature=0,
        model="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


def get_llm_response(prompt: str, role: str = "unknown", query: str = "") -> dict:
    """
    Invoke the LLM and return:
      {
        "content":    str,
        "usage":      dict,   # prompt/completion/total tokens
        "latency_ms": float,
      }
    """
    llm = get_llm()

    try:
        t0 = time.time()
        response = llm.invoke(prompt)
        latency_ms = round((time.time() - t0) * 1000, 1)

        # ── Extract token usage ────────────────────────────────────────
        usage = {}
        meta  = getattr(response, "response_metadata", {})
        raw   = meta.get("token_usage") or meta.get("usage") or {}

        usage = {
            "prompt_tokens":     raw.get("prompt_tokens",     0),
            "completion_tokens": raw.get("completion_tokens", 0),
            "total_tokens":      raw.get("total_tokens",      0),
        }

        # ── Record to token tracker ───────────────────────────────────
        token_tracker.record_usage(usage, role=role, query_preview=query)

        return {
            "content":    response.content.strip(),
            "usage":      usage,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        return {
            "content":    f"Error: {str(e)}",
            "usage":      {},
            "latency_ms": 0,
        }

def get_llm_stream(prompt: str, role: str = "unknown", query: str = ""):
    """
    Generator that yields chunks of content.
    """
    llm = get_llm()
    t0 = time.time()
    
    try:
        for chunk in llm.stream(prompt):
            content = chunk.content
            yield content
            
        latency_ms = round((time.time() - t0) * 1000, 1)
        # Record usage if possible
        token_tracker.record_usage({"total_tokens": 100}, role=role, query_preview=query)
        
    except Exception as e:
        yield f"\n[Error in LLM Stream]: {str(e)}"