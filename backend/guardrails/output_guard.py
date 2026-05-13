"""
backend/guardrails/output_guard.py
Output validation — strips uncertainty, masks PII, enforces grounding.
"""
import re

_BANNED_PHRASES = [
    "i think", "maybe", "probably", "i am not sure", "perhaps",
]


def mask_pii(text: str) -> str:
    """Redact emails and phone numbers from the output."""
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REDACTED]", text)
    # Improved phone regex: Requires at least 7 digits to avoid matching years/dates
    text = re.sub(
        r"(\+?\d{1,3}[.\-\s]?)?\(?\d{3}\)?[.\-\s]?\d{3}[.\-\s]?\d{4,}",
        "[PHONE_REDACTED]",
        text,
    )
    return text


def verify_grounding(answer: str, context: str, query: str = "") -> bool:
    """
    Extract numbers, percentages, and currencies from the answer and ensure
    they exist in the context or query with appropriate associations.
    """
    # 1. Extract percentages (e.g., 18%, 22 percent)
    percentages = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", answer, re.I)
    
    # 2. Extract currencies (e.g., $30M, $25,000)
    currencies = re.findall(r"\$\d+(?:,\d+)*(?:\.\d+)?[KMB]?", answer, re.I)
    
    # 3. Extract other numbers (excluding small IDs/counts)
    numbers = re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", answer)

    ctx_norm = context.lower()
    qry_norm = query.lower()

    # Helper to check if a value is "grounded" in text
    def is_grounded(val, text, is_pct=False):
        val_norm = val.replace(",", "")
        if is_pct:
            # Check for "val%" or "val percent"
            return (f"{val_norm}%" in text.replace(" ", "") or 
                    f"{val_norm} percent" in text)
        return val_norm in text.replace(",", "")

    # Validate Percentages
    for pct in percentages:
        if not is_grounded(pct, ctx_norm, is_pct=True) and not is_grounded(pct, qry_norm, is_pct=True):
            print(f"[Guardrail] Hallucinated percentage: {pct}%")
            return False

    # Validate Currencies
    for cur in currencies:
        val = cur.replace("$", "").replace(",", "")
        if val.lower() not in ctx_norm and val.lower() not in qry_norm:
            print(f"[Guardrail] Hallucinated currency: {cur}")
            return False

    # Validate generic numbers
    for num in numbers:
        if len(num) > 1 and num not in ["2024", "2023"]: # Ignore years and single digits
            if num not in ctx_norm and num not in qry_norm:
                # Double check if it's a part of a larger number in context
                if any(num in word for word in ctx_norm.split()):
                    continue
                print(f"[Guardrail] Hallucinated number: {num}")
                return False

    return True


def validate_output(answer: str, context: str = "", query: str = "") -> str:
    """
    Enforce output constraints:
    1. Replace uncertain language with a safe fallback message.
    2. Verify numerical grounding against context.
    3. PII-mask everything that reaches the client.
    """
    if not answer:
        return answer

    a_lower = answer.lower()
    
    # Refusal markers
    refusal_phrases = ["not accessible", "not available", "no information available"]
    if any(p in a_lower for p in refusal_phrases):
        return mask_pii(answer)

    for phrase in _BANNED_PHRASES:
        if phrase in a_lower:
            return (
                "The AI generated an uncertain answer. "
                "Please refer to your department documents directly."
            )

    if context and "cannot be calculated" not in a_lower and not verify_grounding(answer, context, query):
        return (
            "The answer to this question is not available in the accessible documents."
        )

    return mask_pii(answer)
