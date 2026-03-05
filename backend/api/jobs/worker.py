"""Async task runner that wraps callables as tracked jobs."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from api.jobs.manager import JobManager
from api.jobs.models import JobStatus


async def run_job(
    manager: JobManager,
    job_id: str,
    fn: Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[Any]],
) -> None:
    """Execute an async callable as a tracked job.

    The callable receives a progress callback: ``async def update(pct, step)``.
    """
    async def update(progress: int, step: str) -> None:
        manager.update_progress(job_id, progress, step)

    try:
        manager.update_progress(job_id, 0, None)
        result = await fn(update)
        manager.complete_job(job_id, result)
    except asyncio.CancelledError:
        manager.fail_job(job_id, "Job cancelled")
        raise
    except Exception as exc:
        manager.fail_job(job_id, str(exc))
