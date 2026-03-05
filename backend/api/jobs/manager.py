"""In-memory job manager for tracking background operations."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from api.jobs.models import Job, JobStatus


class JobManager:
    """Manages the lifecycle of background jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

    def create_job(self, job_type: str) -> Job:
        """Create a new job with pending status."""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.pending,
            progress=0,
            created_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = job
        self._events[job_id] = asyncio.Event()
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Return the job for the given id, or None."""
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int, current_step: str | None = None) -> None:
        """Update a job's progress and optionally current step."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.status = JobStatus.running
        job.progress = progress
        job.current_step = current_step
        self._notify(job_id)

    def complete_job(self, job_id: str, result: object = None) -> None:
        """Mark a job as completed with an optional result."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.status = JobStatus.completed
        job.progress = 100
        job.result = result
        job.current_step = None
        self._notify(job_id)

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed with an error message."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.status = JobStatus.failed
        job.error = error
        self._notify(job_id)

    def register_task(self, job_id: str, task: asyncio.Task) -> None:  # type: ignore[type-arg]
        """Register an asyncio task for a job (for cancellation)."""
        self._tasks[job_id] = task

    def get_event(self, job_id: str) -> asyncio.Event | None:
        """Return the asyncio Event for a job, or None."""
        return self._events.get(job_id)

    async def cancel_all(self) -> None:
        """Cancel all running tasks and wait for them to finish."""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    def _notify(self, job_id: str) -> None:
        """Signal that a job's state has changed."""
        event = self._events.get(job_id)
        if event is not None:
            event.set()
