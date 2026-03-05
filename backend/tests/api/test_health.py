"""Tests for GET /health endpoint."""

from __future__ import annotations

import pytest

import api


@pytest.mark.asyncio
async def test_health_returns_200_with_status_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_current_version(client):
    resp = await client.get("/health")
    data = resp.json()
    assert data["version"] == api.__version__


@pytest.mark.asyncio
async def test_health_content_type_is_json(client):
    resp = await client.get("/health")
    assert resp.headers["content-type"] == "application/json"
