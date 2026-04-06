# python-task-worker

![CI](https://github.com/Shaisolaris/python-task-worker/actions/workflows/ci.yml/badge.svg)

Celery task worker system with Redis broker, task routing across 4 queues, retry with exponential backoff, scheduled tasks via Beat, dead letter handling, rate limiting, and a FastAPI monitoring dashboard. Includes email, data processing, notification, and maintenance task modules.

## Stack

- **Task Queue:** Celery 5.4+ with Redis broker and result backend
- **Monitoring:** FastAPI dashboard + Flower (optional)
- **Scheduling:** Celery Beat with crontab and interval schedules

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Producers   │────▶│    Redis     │────▶│  Celery Workers  │
│ (API/App)    │     │   Broker    │     │  (4 queues)      │
└─────────────┘     └─────────────┘     └──────────────────┘
                          │                       │
                    ┌─────▼─────┐          ┌──────▼──────┐
                    │  Results  │          │  Beat       │
                    │  Backend  │          │  Scheduler  │
                    └───────────┘          └─────────────┘
```

## Task Queues

| Queue | Tasks | Rate Limit |
|---|---|---|
| `email` | send_email, send_bulk_email, send_template_email | 30/min per task |
| `data` | generate_report, import_csv, export_data, aggregate_metrics | 10/min |
| `notifications` | send_push, send_sms, dispatch_webhook | 100/min (push), 10/min (SMS) |
| `maintenance` | cleanup_expired_results, cleanup_old_files, health_check, rotate_logs | No limit |

## Tasks

### Email Tasks (`tasks/email_tasks.py`)
- `send_email` — Single email with retry (3x exponential backoff), dead letter on permanent failure
- `send_bulk_email` — Batch emails with configurable batch size, queues individual sends
- `send_template_email` — Render from template (welcome, reset_password, invoice) then send

### Data Tasks (`tasks/data_tasks.py`)
- `generate_report` — Async report generation with soft/hard time limits (5min/6min)
- `generate_daily_report` — Scheduled daily at 8 AM UTC via Beat
- `import_csv` — CSV import with row count, skip count, error tracking
- `export_data` — Data export to CSV/JSON with file URL response
- `aggregate_metrics` — Metric aggregation for reporting periods

### Notification Tasks (`tasks/notification_tasks.py`)
- `send_push` — Push notification via FCM with rate limiting
- `send_sms` — SMS via Twilio with 3 retries, 30s delay
- `dispatch_webhook` — Outbound webhook with SHA-256 signature

### Cleanup Tasks (`tasks/cleanup_tasks.py`)
- `cleanup_expired_results` — Scheduled every 6 hours via Beat
- `cleanup_old_files` — Remove export files older than N days
- `health_check` — Scheduled every 5 minutes, validates worker responsiveness
- `rotate_logs` — Log file rotation

## Scheduled Tasks (Beat)

| Schedule | Task | Description |
|---|---|---|
| Every 6 hours | `cleanup_expired_results` | Remove stale results from Redis |
| Daily 8 AM UTC | `generate_daily_report` | Automated daily summary |
| Every 5 minutes | `health_check` | Worker liveness ping |

## Monitoring Dashboard (FastAPI)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Worker connectivity and count |
| POST | `/tasks` | Submit task by name with args/kwargs |
| GET | `/tasks/{id}` | Task status and result |
| POST | `/tasks/{id}/revoke` | Revoke pending/running task |
| GET | `/workers` | List workers with active tasks and queues |
| GET | `/queues` | Queue lengths (active, reserved, scheduled) |
| GET | `/tasks/registered/list` | All registered task names |
| POST | `/tasks/purge/{queue}` | Purge queue messages |

## File Structure

```
python-task-worker/
├── main.py                        # CLI: worker, beat, dashboard, flower
├── workers/
│   └── celery_app.py              # Celery config, routing, beat schedule
├── tasks/
│   ├── email_tasks.py             # Email: single, bulk, template, dead letter
│   ├── data_tasks.py              # Reports, imports, exports, aggregations
│   ├── notification_tasks.py      # Push, SMS, webhooks
│   └── cleanup_tasks.py           # Maintenance: cleanup, health, logs
├── api/
│   └── dashboard.py               # FastAPI monitoring endpoints
├── requirements.txt
└── pyproject.toml
```

## Setup

```bash
git clone https://github.com/Shaisolaris/python-task-worker.git
cd python-task-worker
pip install -r requirements.txt

# Start Redis
redis-server

# Start worker (processes all queues)
python main.py worker

# Start beat scheduler (separate terminal)
python main.py beat

# Start monitoring dashboard (separate terminal)
python main.py dashboard
# → http://localhost:8000/docs
```

## Key Design Decisions

**4 dedicated queues.** Tasks are routed to queues by module: email, data, notifications, maintenance. This enables independent scaling (more email workers during campaigns), priority management, and queue-specific rate limits. Workers can consume specific queues or all of them.

**Exponential backoff retries.** Email tasks use `countdown=60 * (2 ** retries)` for backoff: 1min, 2min, 4min. This prevents thundering herd on transient failures while still retrying quickly enough to deliver within SLA.

**Dead letter handling.** Non-retryable failures call `_dead_letter()` which logs the failed task payload. In production, this writes to a Redis list or database table for manual review and replay.

**Task acknowledgment after execution.** `acks_late=True` ensures tasks are re-delivered if the worker crashes mid-execution. Combined with `reject_on_worker_lost=True`, this provides at-least-once delivery semantics.

**Soft and hard time limits.** Data processing tasks set both `soft_time_limit` (raises SoftTimeLimitExceeded, allowing cleanup) and `time_limit` (hard kill). Report generation gets 5min soft / 6min hard to handle large datasets gracefully.

**FastAPI dashboard over Flower for API access.** While Flower provides a web UI, the FastAPI dashboard exposes programmatic task submission, status checks, and queue management via REST API. This enables integration with other services and custom monitoring.

## License

MIT
