"""Job lifecycle models for background task tracking."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, enum.Enum):
    """Lifecycle state of a background job."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(BaseModel):
    """A single background operation tracked by the job manager."""

    job_id: str
    job_type: str
    status: JobStatus = JobStatus.pending
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str | None = None
    result: Any = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobEvent(BaseModel):
    """WebSocket message representing a job state snapshot."""

    event: str
    job_id: str
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str | None = None
    result: Any = None
    error: str | None = None
