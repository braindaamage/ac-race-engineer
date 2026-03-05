"""Tests for run_job worker."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import pytest

from api.jobs.manager import JobManager
from api.jobs.models import JobStatus
from api.jobs.worker import run_job


@pytest.fixture
def mgr() -> JobManager:
    return JobManager()


@pytest.mark.asyncio
async def test_successful_job_reports_progress_and_completes(mgr):
    """A successful mock callable that reports 3 progress steps ends as completed."""
    async def work(update: Callable[[int, str], Awaitable[None]]) -> dict[str, Any]:
        await update(33, "Step 1")
        await update(66, "Step 2")
        await update(100, "Step 3")
        return {"done": True}

    job = mgr.create_job("test")
    await run_job(mgr, job.job_id, work)

    result = mgr.get_job(job.job_id)
    assert result.status == JobStatus.completed
    assert result.result == {"done": True}


@pytest.mark.asyncio
async def test_failing_job_ends_as_failed(mgr):
    """A callable that raises ends the job as failed with error message."""
    async def work(update: Callable[[int, str], Awaitable[None]]) -> None:
        await update(50, "Working")
        raise ValueError("Something went wrong")

    job = mgr.create_job("test")
    await run_job(mgr, job.job_id, work)

    result = mgr.get_job(job.job_id)
    assert result.status == JobStatus.failed
    assert "Something went wrong" in result.error


@pytest.mark.asyncio
async def test_cancelled_job_ends_as_failed(mgr):
    """A cancelled job should end as failed."""
    async def work(update: Callable[[int, str], Awaitable[None]]) -> None:
        await update(10, "Starting")
        await asyncio.sleep(100)  # will be cancelled

    job = mgr.create_job("test")
    task = asyncio.create_task(run_job(mgr, job.job_id, work))

    # Give the task a moment to start
    await asyncio.sleep(0.05)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    result = mgr.get_job(job.job_id)
    assert result.status == JobStatus.failed
