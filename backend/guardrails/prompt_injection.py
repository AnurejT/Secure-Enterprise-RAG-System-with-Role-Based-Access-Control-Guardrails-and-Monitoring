"""
backend/guardrails/prompt_injection.py
Prompt injection detection — blocks attempts to override system instructions.
"""
import re

_INJECTION_PATTERNS = [
    r"ignore (all |previous |above |prior )?instructions",
    r"disregard (the |your |all )?instructions",
    r"forget (everything|all|your instructions)",
    r"you are now",
    r"act as (a |an )?",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"DAN mode",
    r"override (your |the )?system",
    r"new persona",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def detect_injection(query: str) -> tuple[bool, str]:
    """
    Returns (is_injected, reason).
    is_injected=True means the query looks like a prompt injection attack.
    """
    for pattern in _COMPILED:
        if pattern.search(query):
            return True, "Query blocked: possible prompt injection detected."
    return False, ""
