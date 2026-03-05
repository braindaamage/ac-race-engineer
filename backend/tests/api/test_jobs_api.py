"""Tests for GET /jobs/{job_id} endpoint."""

from __future__ import annotations

import pytest

from api.jobs.models import JobStatus


@pytest.mark.asyncio
async def test_get_existing_job_returns_200(client, manager):
    job = manager.create_job("parse")
    resp = await client.get(f"/jobs/{job.job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job.job_id
    assert data["job_type"] == "parse"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_unknown_job_returns_404(client, manager):
    resp = await client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["type"] == "not_found"
