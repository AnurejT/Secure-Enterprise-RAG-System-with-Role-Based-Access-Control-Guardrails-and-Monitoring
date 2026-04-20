"""
LangSmith Tracer — wraps LLM calls with run tracking.
Requires: LANGCHAIN_API_KEY, LANGCHAIN_PROJECT in .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


def configure_langsmith():
    """
    Enable LangSmith tracing by setting env vars.
    Call once at app startup.
    """
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project  = os.getenv("LANGCHAIN_PROJECT", "enterprise-rag")

    if not api_key:
        print("[LangSmith] WARNING: LANGCHAIN_API_KEY not set - tracing disabled.")
        return False

    os.environ["LANGCHAIN_TRACING_V2"]    = "true"
    os.environ["LANGCHAIN_API_KEY"]        = api_key
    os.environ["LANGCHAIN_PROJECT"]        = project
    os.environ["LANGCHAIN_ENDPOINT"]       = "https://api.smith.langchain.com"

    print(f"[LangSmith] Tracing enabled - project: '{project}'")
    return True


def is_langsmith_enabled() -> bool:
    return os.getenv("LANGCHAIN_TRACING_V2") == "true" and bool(os.getenv("LANGCHAIN_API_KEY"))
