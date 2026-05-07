"""
backend/monitoring/tracer.py
LangSmith tracing setup — call once at app startup.
"""
import os
from backend.core import config


def configure_langsmith() -> bool:
    if not config.LANGCHAIN_API_KEY:
        print("[LangSmith] WARNING: LANGCHAIN_API_KEY not set — tracing disabled.")
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = config.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"]    = config.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"]   = "https://api.smith.langchain.com"

    print(f"[LangSmith] Tracing enabled — project: '{config.LANGCHAIN_PROJECT}'")
    return True


def is_enabled() -> bool:
    return os.getenv("LANGCHAIN_TRACING_V2") == "true" and bool(os.getenv("LANGCHAIN_API_KEY"))
