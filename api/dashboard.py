"""FastAPI monitoring dashboard for Celery tasks."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from workers.celery_app import app as celery_app

logger = logging.getLogger(__name__)

app = FastAPI(title="Task Worker Dashboard", version="1.0.0")


class TaskSubmitRequest(BaseModel):
    task_name: str = Field(..., description="Full task name e.g. tasks.email_tasks.send_email")
    args: list[Any] = Field(default=[], description="Positional arguments")
    kwargs: dict[str, Any] = Field(default={}, description="Keyword arguments")
    queue: str | None = Field(default=None, description="Override queue routing")
    countdown: int | None = Field(default=None, description="Delay in seconds before execution")
    priority: int | None = Field(default=None, description="Task priority (0-9)")


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None
    error: str | None = None


class WorkerInfo(BaseModel):
    name: str
    status: str
    active_tasks: int
    processed: int
    queues: list[str]


# ─── Endpoints ───────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    """Check API and Celery connectivity."""
    try:
        inspect = celery_app.control.inspect()
        ping = inspect.ping()
        workers = list(ping.keys()) if ping else []
        return {"status": "healthy", "workers": len(workers), "worker_names": workers}
    except Exception as e:
        return {"status": "degraded", "error": str(e), "workers": 0}


@app.post("/tasks", response_model=TaskStatusResponse)
def submit_task(request: TaskSubmitRequest) -> TaskStatusResponse:
    """Submit a task for execution."""
    try:
        result = celery_app.send_task(
            request.task_name,
            args=request.args,
            kwargs=request.kwargs,
            queue=request.queue,
            countdown=request.countdown,
            priority=request.priority,
        )
        return TaskStatusResponse(task_id=result.id, status="PENDING")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get task status and result."""
    result = celery_app.AsyncResult(task_id)
    response = TaskStatusResponse(task_id=task_id, status=result.status)

    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.error = str(result.result)

    return response


@app.post("/tasks/{task_id}/revoke")
def revoke_task(task_id: str, terminate: bool = False) -> dict:
    """Revoke a pending or running task."""
    celery_app.control.revoke(task_id, terminate=terminate)
    return {"task_id": task_id, "revoked": True, "terminated": terminate}


@app.get("/workers")
def list_workers() -> list[WorkerInfo]:
    """List active Celery workers."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        active_queues = inspect.active_queues() or {}

        workers = []
        for name, info in stats.items():
            queues = [q["name"] for q in active_queues.get(name, [])]
            workers.append(WorkerInfo(
                name=name,
                status="online",
                active_tasks=len(active.get(name, [])),
                processed=info.get("total", {}).get("tasks.email_tasks.send_email", 0),
                queues=queues,
            ))
        return workers
    except Exception:
        return []


@app.get("/queues")
def queue_stats() -> dict[str, Any]:
    """Get queue lengths and active task counts."""
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        scheduled = inspect.scheduled() or {}

        return {
            "active": {k: len(v) for k, v in active.items()},
            "reserved": {k: len(v) for k, v in reserved.items()},
            "scheduled": {k: len(v) for k, v in scheduled.items()},
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/tasks/registered/list")
def registered_tasks() -> list[str]:
    """List all registered task names."""
    try:
        inspect = celery_app.control.inspect()
        registered = inspect.registered() or {}
        tasks: set[str] = set()
        for worker_tasks in registered.values():
            tasks.update(worker_tasks)
        return sorted(tasks)
    except Exception:
        return []


@app.post("/tasks/purge/{queue}")
def purge_queue(queue: str) -> dict:
    """Purge all messages from a queue."""
    try:
        count = celery_app.control.purge()
        return {"queue": queue, "purged": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
