from celery import Celery
from backend.core import config

def make_celery(app_name="enterprise_rag"):
    celery_instance = Celery(
        app_name,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND
    )
    
    celery_instance.conf.update(
        task_serializer=config.CELERY_TASK_SERIALIZER,
        accept_content=config.CELERY_ACCEPT_CONTENT,
        result_serializer=config.CELERY_RESULT_SERIALIZER,
        timezone=config.CELERY_TIMEZONE,
        task_track_started=config.CELERY_TASK_TRACK_STARTED,
        task_time_limit=config.CELERY_TASK_TIME_LIMIT,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )
    
    return celery_instance

celery = make_celery()
