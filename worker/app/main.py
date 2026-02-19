"""
Worker entry point.

Architecture:
- Uses RQ (Redis Queue) for job enqueueing.
- A separate "scheduler loop" runs in the main thread and enqueues
  jobs on a fixed interval.  This keeps the approach simple without
  requiring rq-scheduler or a cron daemon.
- RQ worker runs in a subprocess and picks up jobs from the queue.

Start with:   python -m app.main
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from multiprocessing import Process

import structlog
from redis import Redis
from rq import Queue, Worker

from app.config import get_worker_settings

settings = get_worker_settings()


def _configure_logging() -> None:
    import sys

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    )


log = structlog.get_logger("worker.main")


def _get_redis() -> Redis:  # type: ignore[type-arg]
    return Redis.from_url(settings.redis_url)


# ── RQ Worker process ─────────────────────────────────────────────────────────

def _run_rq_worker() -> None:
    """Run the RQ worker (blocking). Called in a subprocess."""
    _configure_logging()
    redis_conn = _get_redis()
    q = Queue(connection=redis_conn)
    worker = Worker([q], connection=redis_conn)
    worker.work(with_scheduler=False)


# ── Scheduler loop ────────────────────────────────────────────────────────────

SYNC_TASKS = [
    ("app.tasks.sync_fixtures_task", 300),       # every 5 min
    ("app.tasks.sync_standings_task", 1800),     # every 30 min
    ("app.tasks.sync_live_events_task", 60),     # every 1 min
]


def _run_scheduler() -> None:
    """Enqueues periodic tasks via RQ. Blocks forever."""
    _configure_logging()
    redis_conn = _get_redis()
    q = Queue(connection=redis_conn)

    # Track last enqueue time per task
    last_run: dict[str, float] = {name: 0.0 for name, _ in SYNC_TASKS}

    log.info("Scheduler loop started", interval_seconds=settings.worker_sync_interval_seconds)

    while True:
        now = time.monotonic()
        for task_path, interval in SYNC_TASKS:
            if now - last_run[task_path] >= interval:
                q.enqueue(task_path)
                last_run[task_path] = now
                log.info("Enqueued task", task=task_path)
        time.sleep(10)  # check every 10 s


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _configure_logging()
    log.info(
        "MyTeams worker starting",
        env=settings.app_env,
        provider=settings.provider_name,
        sync_interval=settings.worker_sync_interval_seconds,
    )

    # Start RQ worker in a daemon subprocess
    worker_proc = Process(target=_run_rq_worker, daemon=True)
    worker_proc.start()
    log.info("RQ worker subprocess started", pid=worker_proc.pid)

    # Handle graceful shutdown
    def _shutdown(signum: int, frame: object) -> None:
        log.info("Received signal, shutting down", signum=signum)
        worker_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Run scheduler in main thread (blocks)
    try:
        _run_scheduler()
    except KeyboardInterrupt:
        log.info("Scheduler interrupted")
    finally:
        worker_proc.terminate()


if __name__ == "__main__":
    main()
