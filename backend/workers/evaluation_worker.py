"""
backend/workers/evaluation_worker.py
Background thread worker that runs Ragas evaluation asynchronously.
Renamed from ragas_worker.py; imports updated to monitoring.service.
"""
import threading
from backend.monitoring.service import evaluate_and_record


def run_eval_async(
    query:       str,
    answer:      str,
    contexts:    list,
    role:        str,
    token_usage: dict  = None,
    latency_ms:  float = None,
) -> None:
    """
    Spawn a daemon thread to evaluate and record Ragas scores.
    The HTTP request returns immediately; eval happens in the background.
    """
    def _worker():
        try:
            evaluate_and_record(
                query=query,
                answer=answer,
                contexts=contexts,
                role=role,
                token_usage=token_usage,
                latency_ms=latency_ms,
            )
        except Exception as e:
            print(f"[EvaluationWorker] Background eval failed: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
