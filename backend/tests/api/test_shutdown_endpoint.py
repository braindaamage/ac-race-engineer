"""Tests for POST /shutdown endpoint."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_post_shutdown_returns_200(client):
    resp = await client.post("/shutdown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "shutting_down"


@pytest.mark.asyncio
async def test_get_shutdown_returns_405(client):
    resp = await client.get("/shutdown")
    assert resp.status_code == 405
