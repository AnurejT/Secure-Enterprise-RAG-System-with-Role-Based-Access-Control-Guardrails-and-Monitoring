import os
import traceback
from celery import shared_task
from backend.rag.ingestion.document_ingestor import ingest_document
from backend.core.logger import logger

@shared_task(bind=True, max_retries=3)
def ingest_document_task(self, file_path: str, role: str):
    """
    Background task to process a document.
    Updates state to allow frontend tracking.
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'Starting ingestion...'})
        
        # We pass self to ingest_document if we want detailed progress, 
        # but for now we'll just wrap the call.
        success = ingest_document(file_path, role, task=self)
        
        if success:
            return {'status': 'COMPLETED', 'progress': 100, 'message': 'File indexed successfully'}
        else:
            raise Exception("Ingestion returned False")
            
    except Exception as exc:
        logger.error(f"Ingestion task failed for {file_path}: {exc}")
        # Retry logic for transient failures (e.g. embedding API timeouts)
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60)
        
        return {
            'status': 'FAILED',
            'progress': 0,
            'error': str(exc),
            'traceback': traceback.format_exc()
        }
