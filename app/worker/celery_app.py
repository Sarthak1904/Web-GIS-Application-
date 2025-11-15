"""Celery application configuration."""

from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "geospatial",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Fair distribution
)
