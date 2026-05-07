"""
backend/monitoring/service.py
Façade that ties together Ragas evaluation + metrics persistence.
Moved from services/monitoring_service.py.
"""
from backend.monitoring.evaluator import run_ragas_eval_safe
from backend.monitoring import repository


def evaluate_and_record(
    query:       str,
    answer:      str,
    contexts:    list,
    role:        str,
    token_usage: dict  = None,
    latency_ms:  float = None,
) -> dict:
    """
    Run Ragas eval and persist results in repository.
    Returns the scores dict.
    """
    scores = run_ragas_eval_safe(question=query, answer=answer, contexts=contexts)

    repository.record_eval(
        query=query,
        answer=answer,
        role=role,
        scores=scores,
        token_usage=token_usage,
        latency_ms=latency_ms,
    )

    return scores
