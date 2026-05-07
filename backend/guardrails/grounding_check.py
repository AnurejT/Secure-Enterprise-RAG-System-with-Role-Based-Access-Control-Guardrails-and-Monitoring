"""
backend/guardrails/grounding_check.py
Grounding check — verifies that an answer is supported by the retrieved context.
"""


def is_grounded(answer: str, context: str, min_overlap: float = 0.1) -> bool:
    """
    Simple lexical grounding check.
    Returns True if enough answer words appear in the context.
    """
    if not answer or not context:
        return False

    answer_words  = set(answer.lower().split())
    context_words = set(context.lower().split())

    # Remove common stop words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "not", "this", "that"}
    answer_words  -= stop_words
    context_words -= stop_words

    if not answer_words:
        return True  # trivially grounded

    overlap = len(answer_words & context_words) / len(answer_words)
    return overlap >= min_overlap


def check_grounding(answer: str, context: str) -> tuple[bool, str]:
    """
    Returns (is_grounded, warning_message).
    """
    grounded = is_grounded(answer, context)
    if not grounded:
        return False, "Answer may not be grounded in the provided documents."
    return True, ""
