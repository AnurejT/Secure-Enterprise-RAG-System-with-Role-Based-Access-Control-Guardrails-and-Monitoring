"""
backend/guardrails/pii_masking.py
Dedicated PII masking utilities — email, phone, employee IDs.
"""
import re


def mask_emails(text: str) -> str:
    return re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REDACTED]", text)


def mask_phones(text: str) -> str:
    return re.sub(
        r"\+?\d{1,4}?[.\-\s]?\(?\d{1,3}?\)?[.\-\s]?\d{1,4}[.\-\s]?\d{1,4}[.\-\s]?\d{1,9}",
        "[PHONE_REDACTED]",
        text,
    )


def mask_employee_ids(text: str) -> str:
    return re.sub(r"FINEMP\d+", "[EMP_ID]", text, flags=re.IGNORECASE)


def mask_all(text: str) -> str:
    """Apply all PII masks in sequence."""
    text = mask_emails(text)
    text = mask_phones(text)
    text = mask_employee_ids(text)
    return text
