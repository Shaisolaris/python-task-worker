"""Celery application configuration with task routing and scheduling."""

from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab

# ─── App Setup ───────────────────────────────────────────

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "task_worker",
    broker=broker_url,
    backend=result_backend,
    include=[
        "tasks.email_tasks",
        "tasks.data_tasks",
        "tasks.notification_tasks",
        "tasks.cleanup_tasks",
    ],
)

# ─── Configuration ───────────────────────────────────────

app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Result backend
    result_expires=3600,  # 1 hour

    # Retry defaults
    task_default_retry_delay=60,
    task_max_retries=3,

    # Rate limiting
    task_default_rate_limit="100/m",

    # Task routing
    task_routes={
        "tasks.email_tasks.*": {"queue": "email"},
        "tasks.data_tasks.*": {"queue": "data"},
        "tasks.notification_tasks.*": {"queue": "notifications"},
        "tasks.cleanup_tasks.*": {"queue": "maintenance"},
    },


    # Beat schedule
    beat_schedule={
        "cleanup-expired-results": {
            "task": "tasks.cleanup_tasks.cleanup_expired_results",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "generate-daily-report": {
            "task": "tasks.data_tasks.generate_daily_report",
            "schedule": crontab(minute=0, hour=8),  # 8 AM UTC
        },
        "health-check-ping": {
            "task": "tasks.cleanup_tasks.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)
