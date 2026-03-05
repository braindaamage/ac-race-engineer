"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from api.jobs.manager import JobManager


def get_job_manager(request: Request) -> JobManager:
    """FastAPI dependency that returns the app-wide JobManager."""
    return request.app.state.job_manager
