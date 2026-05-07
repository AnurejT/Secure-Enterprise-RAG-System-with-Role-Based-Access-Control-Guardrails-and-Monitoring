"""
backend/workers/ingestion_worker.py
Background worker for async document ingestion tasks.
"""
import threading
from backend.rag.ingestion.document_ingestor import ingest_document


def run_ingestion_async(file_path: str, role: str) -> None:
    """Spawn a daemon thread to ingest a document asynchronously."""
    def _worker():
        try:
            ingest_document(file_path, role)
        except Exception as e:
            print(f"[IngestionWorker] Background ingestion failed: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
