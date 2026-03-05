"""Tests for CORS middleware."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_preflight_from_localhost_returns_cors_headers(client):
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.asyncio
async def test_actual_request_from_localhost_includes_cors(client):
    resp = await client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_request_from_non_localhost_has_no_cors(client):
    resp = await client.get(
        "/health",
        headers={"Origin": "http://example.com"},
    )
    assert resp.headers.get("access-control-allow-origin") is None
