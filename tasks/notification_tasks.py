"""Notification tasks — push, SMS, webhook dispatch."""

from __future__ import annotations

import logging
import time
from typing import Any

from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    name="tasks.notification_tasks.send_push",
    rate_limit="100/m",
    max_retries=2,
)
def send_push(user_id: str, title: str, body: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a push notification."""
    logger.info(f"Push notification to {user_id}: {title}")
    time.sleep(0.05)
    return {"user_id": user_id, "title": title, "status": "delivered", "provider": "fcm"}


@app.task(
    name="tasks.notification_tasks.send_sms",
    rate_limit="10/m",
    max_retries=3,
    default_retry_delay=30,
)
def send_sms(phone: str, message: str) -> dict[str, Any]:
    """Send an SMS message."""
    logger.info(f"SMS to {phone}: {message[:50]}")
    time.sleep(0.1)
    return {"phone": phone, "status": "sent", "provider": "twilio", "message_id": f"sms_{int(time.time())}"}


@app.task(
    bind=True,
    name="tasks.notification_tasks.dispatch_webhook",
    max_retries=3,
    default_retry_delay=10,
)
def dispatch_webhook(self, url: str, event: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a webhook to an external URL."""
    import hashlib
    import json

    logger.info(f"Webhook to {url}: {event}")
    time.sleep(0.1)

    body = json.dumps({"event": event, "payload": payload, "timestamp": time.time()})
    signature = hashlib.sha256(body.encode()).hexdigest()

    return {"url": url, "event": event, "status": "delivered", "signature": signature[:16], "status_code": 200}
