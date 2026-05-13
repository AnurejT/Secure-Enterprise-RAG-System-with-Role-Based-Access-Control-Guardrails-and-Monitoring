"""
celery_worker.py
Entry point for Celery workers. 
Run with: celery -A celery_worker.celery worker --loglevel=info
"""
from backend.app import create_app
from backend.celery_app import celery

# Create Flask app and push context so tasks have access to DB/Extensions
flask_app = create_app()
flask_app.app_context().push()

# Ensure tasks are registered
import backend.tasks.ingestion_tasks  # noqa
import backend.tasks.eval_tasks       # noqa
