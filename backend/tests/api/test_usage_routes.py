"""Tests for the usage endpoint GET /sessions/{sid}/recommendations/{rid}/usage.

Covers:
- 200 with usage data (aggregated totals + per-agent breakdown)
- 200 with empty usage (recommendation exists, no usage records)
- 404 for nonexistent session
- 404 for nonexistent recommendation
- Domain names in response match agent domains
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import (
    AgentUsage,
    SessionRecord,
    ToolCallDetail,
)
from ac_engineer.storage.models import SetupChange as StorageSetupChange
from ac_engineer.storage.recommendations import save_recommendation
from ac_engineer.storage.sessions import save_session
from ac_engineer.storage.usage import save_agent_usage

from api.jobs.manager import JobManager
from api.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    init_db(path)
    return path


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    p = tmp_path / "config.json"
    p.write_text(
        json.dumps({"llm_provider": "anthropic", "llm_model": "claude-sonnet-4-5"}),
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def app(db_path: Path, sessions_dir: Path, config_path: Path):
    a = create_app()
    a.state.db_path = db_path
    a.state.sessions_dir = sessions_dir
    a.state.config_path = config_path
    a.state.job_manager = JobManager()
    a.state.active_processing_jobs = {}
    a.state.active_engineer_jobs = {}
    return a


@pytest_asyncio.fixture
async def client(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


def _seed_session(db_path, session_id="test_session"):
    save_session(
        db_path,
        SessionRecord(
            session_id=session_id,
            car="test_car",
            track="test_track",
            session_date="2026-03-02T14:00:00",
            lap_count=5,
            best_lap_time=89.5,
            state="analyzed",
        ),
    )


def _seed_recommendation(db_path, session_id="test_session"):
    """Seed a recommendation and return its ID."""
    rec = save_recommendation(
        db_path,
        session_id,
        "Test recommendation summary",
        [
            StorageSetupChange(
                section="PRESSURE_LF",
                parameter="VALUE",
                old_value="26.5",
                new_value="27.0",
                reasoning="Increase pressure",
            ),
        ],
    )
    return rec.recommendation_id


def _seed_usage(db_path, recommendation_id):
    """Seed usage records for a recommendation."""
    usage_balance = AgentUsage(
        recommendation_id=recommendation_id,
        domain="balance",
        model="claude-sonnet-4-5",
        input_tokens=5400,
        output_tokens=1200,
        tool_call_count=3,
        turn_count=2,
        duration_ms=4500,
        tool_calls=[
            ToolCallDetail(tool_name="search_kb", token_count=350),
            ToolCallDetail(tool_name="get_setup_range", token_count=45),
            ToolCallDetail(tool_name="get_current_value", token_count=20),
        ],
    )
    usage_tyre = AgentUsage(
        recommendation_id=recommendation_id,
        domain="tyre",
        model="claude-sonnet-4-5",
        input_tokens=5100,
        output_tokens=1400,
        tool_call_count=3,
        turn_count=2,
        duration_ms=5200,
        tool_calls=[
            ToolCallDetail(tool_name="search_kb", token_count=310),
            ToolCallDetail(tool_name="get_setup_range", token_count=50),
        ],
    )
    save_agent_usage(db_path, usage_balance)
    save_agent_usage(db_path, usage_tyre)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_usage_with_data(client, db_path):
    """200 with usage data — verify aggregated totals and per-agent breakdown."""
    _seed_session(db_path)
    rec_id = _seed_recommendation(db_path)
    _seed_usage(db_path, rec_id)

    resp = await client.get(f"/sessions/test_session/recommendations/{rec_id}/usage")
    assert resp.status_code == 200

    data = resp.json()
    assert data["recommendation_id"] == rec_id

    # Check totals
    totals = data["totals"]
    assert totals["input_tokens"] == 5400 + 5100
    assert totals["output_tokens"] == 1200 + 1400
    assert totals["total_tokens"] == (5400 + 5100) + (1200 + 1400)
    assert totals["tool_call_count"] == 3 + 3
    assert totals["agent_count"] == 2

    # Check per-agent breakdown
    agents = data["agents"]
    assert len(agents) == 2

    domains = [a["domain"] for a in agents]
    assert "balance" in domains
    assert "tyre" in domains

    balance = next(a for a in agents if a["domain"] == "balance")
    assert balance["input_tokens"] == 5400
    assert balance["output_tokens"] == 1200
    assert balance["tool_call_count"] == 3
    assert balance["turn_count"] == 2
    assert balance["duration_ms"] == 4500
    assert len(balance["tool_calls"]) == 3
    assert balance["tool_calls"][0]["tool_name"] == "search_kb"
    assert balance["tool_calls"][0]["token_count"] == 350


@pytest.mark.asyncio
async def test_usage_empty(client, db_path):
    """200 with empty usage — recommendation exists but no usage records."""
    _seed_session(db_path)
    rec_id = _seed_recommendation(db_path)

    resp = await client.get(f"/sessions/test_session/recommendations/{rec_id}/usage")
    assert resp.status_code == 200

    data = resp.json()
    assert data["recommendation_id"] == rec_id
    assert data["totals"]["input_tokens"] == 0
    assert data["totals"]["output_tokens"] == 0
    assert data["totals"]["total_tokens"] == 0
    assert data["totals"]["tool_call_count"] == 0
    assert data["totals"]["agent_count"] == 0
    assert data["agents"] == []


@pytest.mark.asyncio
async def test_usage_404_session(client):
    """404 for nonexistent session."""
    resp = await client.get(
        "/sessions/nonexistent/recommendations/fake_rec/usage"
    )
    assert resp.status_code == 404
    assert "Session not found" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_usage_404_recommendation(client, db_path):
    """404 for nonexistent recommendation."""
    _seed_session(db_path)

    resp = await client.get(
        "/sessions/test_session/recommendations/nonexistent_rec/usage"
    )
    assert resp.status_code == 404
    assert "Recommendation not found" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_usage_domain_names(client, db_path):
    """Verify domain names in response match agent domains."""
    _seed_session(db_path)
    rec_id = _seed_recommendation(db_path)

    # Seed all 4 domains
    for domain in ("balance", "tyre", "aero", "technique"):
        usage = AgentUsage(
            recommendation_id=rec_id,
            domain=domain,
            model="claude-sonnet-4-5",
            input_tokens=1000,
            output_tokens=500,
            tool_call_count=1,
            turn_count=1,
            duration_ms=2000,
        )
        save_agent_usage(db_path, usage)

    resp = await client.get(f"/sessions/test_session/recommendations/{rec_id}/usage")
    assert resp.status_code == 200

    data = resp.json()
    domains = sorted(a["domain"] for a in data["agents"])
    assert domains == ["aero", "balance", "technique", "tyre"]
    assert data["totals"]["agent_count"] == 4
