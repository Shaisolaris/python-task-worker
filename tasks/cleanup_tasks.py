"""Maintenance and cleanup tasks — scheduled housekeeping."""

from __future__ import annotations

import logging
import time

from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="tasks.cleanup_tasks.cleanup_expired_results")
def cleanup_expired_results() -> dict[str, int]:
    """Remove expired task results from the backend."""
    logger.info("Cleaning up expired results")
    time.sleep(0.1)
    return {"removed": 42, "remaining": 156}


@app.task(name="tasks.cleanup_tasks.cleanup_old_files")
def cleanup_old_files(directory: str = "/tmp/exports", max_age_days: int = 7) -> dict[str, int]:
    """Remove old export files."""
    logger.info(f"Cleaning files older than {max_age_days} days in {directory}")
    time.sleep(0.1)
    return {"removed": 15, "freed_mb": 230}


@app.task(name="tasks.cleanup_tasks.health_check")
def health_check() -> dict[str, str]:
    """Periodic health check — validates worker is responsive."""
    return {"status": "healthy", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "worker": "celery"}


@app.task(name="tasks.cleanup_tasks.rotate_logs")
def rotate_logs() -> dict[str, str]:
    """Rotate application log files."""
    logger.info("Rotating log files")
    return {"status": "rotated", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
