from celery import shared_task
from backend.monitoring.service import evaluate_and_record
from backend.core.logger import logger

@shared_task(bind=True, max_retries=2)
def run_ragas_eval_task(
    self,
    query:       str,
    answer:      str,
    contexts:    list,
    role:        str,
    token_usage: dict  = None,
    latency_ms:  float = None,
):
    """
    Background task to run Ragas evaluation.
    """
    try:
        logger.info(f"Starting Ragas evaluation for query: {query[:50]}...")
        scores = evaluate_and_record(
            query=query,
            answer=answer,
            contexts=contexts,
            role=role,
            token_usage=token_usage,
            latency_ms=latency_ms,
        )
        return {'status': 'COMPLETED', 'scores': scores}
    except Exception as exc:
        logger.error(f"Ragas evaluation task failed: {exc}")
        # Retry for possible transient API issues
        raise self.retry(exc=exc, countdown=30)
