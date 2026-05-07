"""
backend/guardrails/input_guard.py
Input validation — blocks malicious, irrelevant, or oversized queries.
"""
import re

_BLOCKED_PATTERNS = [
    r"password",
    r"credit\s*card",
    r"cvv",
    r"bank\s*account",
    r"\bssn\b",
    r"social\s*security",
]

_IRRELEVANT_KEYWORDS = [
    "movie", "song", "cricket", "weather", "recipe",
    "sports", "celebrity", "music",
]

MAX_QUERY_LEN = 500


def validate_input(query: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    is_valid=True means the query is safe to process.
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."

    if len(query) > MAX_QUERY_LEN:
        return False, f"Query exceeds maximum length of {MAX_QUERY_LEN} characters."

    # Prevent extremely short or purely punctuation/gibberish queries from consuming LLM tokens
    alphanumeric_count = sum(c.isalnum() for c in query)
    if alphanumeric_count < 3:
        return False, "Please provide a complete and specific question."

    q_lower = query.lower()

    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, q_lower):
            return False, "Query blocked by security guardrails (sensitive topic)."

    for word in _IRRELEVANT_KEYWORDS:
        if word in q_lower:
            return False, "Query blocked by security guardrails (off-topic)."

    return True, ""
