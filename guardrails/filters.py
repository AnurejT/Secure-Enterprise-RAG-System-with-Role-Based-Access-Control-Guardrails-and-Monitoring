# guardrails/filters.py

import re

# ---------------- INPUT GUARDRAILS ---------------- #

BLOCKED_PATTERNS = [
    r"password",
    r"credit card",
    r"cvv",
    r"bank account",
    r"ssn"
]

def is_malicious_query(query: str) -> bool:
    query = query.lower()
    return any(re.search(p, query) for p in BLOCKED_PATTERNS)


def is_irrelevant_query(query: str) -> bool:
    irrelevant_keywords = ["movie", "song", "cricket", "weather"]
    return any(word in query.lower() for word in irrelevant_keywords)


# ---------------- CONTEXT GUARDRAIL ---------------- #

def check_empty_context(docs):
    return len(docs) == 0


# ---------------- OUTPUT GUARDRAILS ---------------- #

def enforce_output_constraints(answer: str) -> str:
    if not answer:
        return "No information available"

    banned_phrases = ["i think", "maybe", "probably"]

    if any(p in answer.lower() for p in banned_phrases):
        return "Answer not reliable. Please refine your query."

    return answer


# ---------------- COMBINED INPUT GUARDRAIL (used by rag_service) ---------------- #

def input_guardrail(query: str) -> bool:
    """
    Returns True if the query is safe to process, False if it should be blocked.
    """
    if not query or not query.strip():
        return False
    if len(query) > 300:
        return False
    if is_malicious_query(query):
        return False
    if is_irrelevant_query(query):
        return False
    return True