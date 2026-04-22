# guardrails/filters.py
import re

# ---------------- CONFIG ---------------- #

BLOCKED_PATTERNS = [
    r"password",
    r"credit card",
    r"cvv",
    r"bank account",
    r"ssn",
    r"social security"
]

# ---------------- HELPER ---------------- #

def mask_pii(text: str) -> str:
    """
    Masks common PII patterns like emails and phone numbers.
    """
    # Mask Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    # Mask Phone Numbers (simple patterns)
    text = re.sub(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', '[PHONE_REDACTED]', text)
    return text

# ---------------- INPUT GUARDRAILS ---------------- #

def is_malicious_query(query: str) -> bool:
    query = query.lower()
    return any(re.search(p, query) for p in BLOCKED_PATTERNS)

def is_irrelevant_query(query: str) -> bool:
    irrelevant_keywords = ["movie", "song", "cricket", "weather", "recipe"]
    return any(word in query.lower() for word in irrelevant_keywords)

def input_guardrail(query: str) -> bool:
    if not query or not query.strip(): return False
    if len(query) > 500: return False # Increased for enterprise questions
    if is_malicious_query(query): return False
    if is_irrelevant_query(query): return False
    return True

# ---------------- OUTPUT GUARDRAILS ---------------- #

def enforce_output_constraints(answer: str, context: str) -> str:
    if not answer or "no information available" in answer.lower():
        return answer

    # Phase 1: Banned Phrases (Uncertainty)
    banned_phrases = ["i think", "maybe", "probably", "i am not sure", "perhaps"]
    if any(p in answer.lower() for p in banned_phrases):
        return "The AI generated an uncertain answer. Please refer to your department documents directly."

    # Phase 2: Grounding Check (Simple)
    # If the context is small and the answer is long, or vice versa, we could add logic.
    # For now, we PII mask everything before it leaves the server.
    return mask_pii(answer)

# ✅ Implementation for rag_service.py
def validate_input(query: str):
    valid = input_guardrail(query)
    msg = "" if valid else "Query blocked by security guardrails (Malicious or Irrelevant)."
    return valid, msg

def validate_output(answer: str, context: str = "") -> str:
    return enforce_output_constraints(answer, context)