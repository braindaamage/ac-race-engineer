"""Tests for GET /health endpoint."""

from __future__ import annotations

import logging

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


def test_health_access_filter_suppresses_health():
    from api.main import HealthAccessFilter

    f = HealthAccessFilter()
    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0,
        '127.0.0.1:63216 - "GET /health HTTP/1.1" 200 OK', (), None,
    )
    assert f.filter(record) is False


def test_health_access_filter_passes_other_routes():
    from api.main import HealthAccessFilter

    f = HealthAccessFilter()
    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0,
        '127.0.0.1:63216 - "GET /sessions HTTP/1.1" 200 OK', (), None,
    )
    assert f.filter(record) is True
