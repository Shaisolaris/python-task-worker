"""Email tasks — send, bulk send, template rendering."""

from __future__ import annotations

import logging
import time
from typing import Any

from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name="tasks.email_tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
    rate_limit="30/m",
    acks_late=True,
)
def send_email(self, to: str, subject: str, body: str, html: bool = False, attachments: list[str] | None = None) -> dict[str, Any]:
    """Send a single email with retry logic."""
    try:
        logger.info(f"Sending email to {to}: {subject}")
        # Simulate SMTP send
        time.sleep(0.1)

        # Simulate occasional failures for retry demonstration
        if "fail" in subject.lower():
            raise ConnectionError("SMTP server unavailable")

        result = {
            "status": "sent",
            "to": to,
            "subject": subject,
            "message_id": f"msg_{int(time.time())}_{id(self)}",
            "html": html,
            "attachments": len(attachments or []),
        }
        logger.info(f"Email sent: {result['message_id']}")
        return result

    except ConnectionError as exc:
        logger.warning(f"Email send failed (attempt {self.request.retries + 1}): {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    except Exception as exc:
        logger.error(f"Email send error (non-retryable): {exc}")
        # Send to dead letter queue
        _dead_letter(self, exc, {"to": to, "subject": subject})
        raise


@app.task(
    bind=True,
    name="tasks.email_tasks.send_bulk_email",
    max_retries=2,
    rate_limit="5/m",
)
def send_bulk_email(self, recipients: list[str], subject: str, body: str, batch_size: int = 50) -> dict[str, Any]:
    """Send emails to multiple recipients in batches."""
    results = {"total": len(recipients), "sent": 0, "failed": 0, "batches": 0}

    for i in range(0, len(recipients), batch_size):
        batch = recipients[i:i + batch_size]
        results["batches"] += 1

        for to in batch:
            try:
                send_email.delay(to, subject, body)
                results["sent"] += 1
            except Exception as exc:
                logger.error(f"Failed to queue email for {to}: {exc}")
                results["failed"] += 1

    logger.info(f"Bulk email queued: {results}")
    return results


@app.task(name="tasks.email_tasks.send_template_email")
def send_template_email(to: str, template_name: str, context: dict[str, Any]) -> dict[str, Any]:
    """Render and send a template-based email."""
    templates = {
        "welcome": {"subject": "Welcome to the platform!", "body": "Hi {name}, welcome aboard!"},
        "reset_password": {"subject": "Password Reset", "body": "Click here to reset: {link}"},
        "invoice": {"subject": "Invoice #{invoice_id}", "body": "Amount due: ${amount}"},
    }

    template = templates.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    subject = template["subject"].format(**context)
    body = template["body"].format(**context)

    return send_email(to, subject, body, html=True)


def _dead_letter(task, exc: Exception, payload: dict) -> None:
    """Send failed task to dead letter queue for manual review."""
    logger.error(f"Dead letter: task={task.name}, error={exc}, payload={payload}")
    # In production: store in Redis list or database table for manual retry
