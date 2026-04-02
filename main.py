"""Main entry point — start Celery worker, beat scheduler, or monitoring dashboard."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "worker"

    if mode == "worker":
        from workers.celery_app import app
        # Start worker with all queues
        app.worker_main([
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "-Q", "email,data,notifications,maintenance,celery",
        ])

    elif mode == "beat":
        from workers.celery_app import app
        # Start beat scheduler
        app.Beat(loglevel="info").run()

    elif mode == "dashboard":
        import uvicorn
        uvicorn.run("api.dashboard:app", host="0.0.0.0", port=8000, reload=True)

    elif mode == "flower":
        # Start Flower monitoring (requires flower package)
        from workers.celery_app import app
        app.start(["flower", "--port=5555"])

    else:
        print("Usage: python main.py [worker|beat|dashboard|flower]")
        print()
        print("  worker    - Start Celery worker processing all queues")
        print("  beat      - Start Celery Beat scheduler for periodic tasks")
        print("  dashboard - Start FastAPI monitoring dashboard on :8000")
        print("  flower    - Start Flower web UI on :5555")
        sys.exit(1)


if __name__ == "__main__":
    main()
