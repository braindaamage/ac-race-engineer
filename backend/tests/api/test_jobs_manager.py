"""Unit tests for JobManager."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from api.jobs.manager import JobManager
from api.jobs.models import JobStatus


@pytest.fixture
def mgr() -> JobManager:
    return JobManager()


class TestCreateJob:
    def test_returns_job_with_pending_status(self, mgr):
        job = mgr.create_job("parse")
        assert job.status == JobStatus.pending

    def test_returns_job_with_uuid4_id(self, mgr):
        job = mgr.create_job("parse")
        uuid.UUID(job.job_id, version=4)  # raises if invalid

    def test_returns_job_with_correct_type(self, mgr):
        job = mgr.create_job("analyze")
        assert job.job_type == "analyze"

    def test_returns_job_with_zero_progress(self, mgr):
        job = mgr.create_job("parse")
        assert job.progress == 0


class TestUpdateProgress:
    def test_changes_progress_and_step(self, mgr):
        job = mgr.create_job("parse")
        mgr.update_progress(job.job_id, 50, "Segmenting laps")
        updated = mgr.get_job(job.job_id)
        assert updated.progress == 50
        assert updated.current_step == "Segmenting laps"
        assert updated.status == JobStatus.running

    def test_ignores_unknown_job_id(self, mgr):
        mgr.update_progress("nonexistent", 50)  # should not raise


class TestCompleteJob:
    def test_sets_result_and_status(self, mgr):
        job = mgr.create_job("parse")
        mgr.complete_job(job.job_id, {"laps": 15})
        updated = mgr.get_job(job.job_id)
        assert updated.status == JobStatus.completed
        assert updated.progress == 100
        assert updated.result == {"laps": 15}


class TestFailJob:
    def test_sets_error_and_status(self, mgr):
        job = mgr.create_job("parse")
        mgr.fail_job(job.job_id, "CSV parse error")
        updated = mgr.get_job(job.job_id)
        assert updated.status == JobStatus.failed
        assert updated.error == "CSV parse error"


class TestGetJob:
    def test_returns_none_for_unknown_id(self, mgr):
        assert mgr.get_job("nonexistent") is None

    def test_returns_existing_job(self, mgr):
        job = mgr.create_job("parse")
        assert mgr.get_job(job.job_id) is job


class TestCancelAll:
    @pytest.mark.asyncio
    async def test_cancels_running_tasks(self, mgr):
        async def long_task():
            await asyncio.sleep(100)

        job = mgr.create_job("parse")
        task = asyncio.create_task(long_task())
        mgr.register_task(job.job_id, task)

        await mgr.cancel_all()
        assert task.cancelled()


class TestEventNotification:
    @pytest.mark.asyncio
    async def test_event_is_set_on_state_change(self, mgr):
        job = mgr.create_job("parse")
        event = mgr.get_event(job.job_id)
        assert not event.is_set()

        mgr.update_progress(job.job_id, 50, "step")
        assert event.is_set()
