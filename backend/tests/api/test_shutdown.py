"""Tests for graceful shutdown behavior."""

from __future__ import annotations

import asyncio

import pytest

from api.jobs.manager import JobManager


@pytest.mark.asyncio
async def test_cancel_all_cancels_running_jobs():
    """Shutdown cancels running tasks and no tasks leak."""
    mgr = JobManager()

    started = asyncio.Event()

    async def long_running():
        started.set()
        await asyncio.sleep(100)

    job = mgr.create_job("parse")
    task = asyncio.create_task(long_running())
    mgr.register_task(job.job_id, task)

    await started.wait()
    await mgr.cancel_all()

    assert task.cancelled()
    # No tasks remain registered
    assert len(mgr._tasks) == 0
