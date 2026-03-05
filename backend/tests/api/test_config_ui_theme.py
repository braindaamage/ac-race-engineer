"""Tests for ui_theme in config API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from ac_engineer.storage.db import init_db
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
    return tmp_path / "config.json"


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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetConfigUITheme:
    @pytest.mark.asyncio
    async def test_returns_ui_theme_default(self, client):
        resp = await client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ui_theme"] == "dark"

    @pytest.mark.asyncio
    async def test_returns_existing_ui_theme(self, client, config_path):
        config_path.write_text(
            json.dumps({"llm_provider": "anthropic", "ui_theme": "light"}),
            encoding="utf-8",
        )
        resp = await client.get("/config")
        assert resp.status_code == 200
        assert resp.json()["ui_theme"] == "light"


class TestPatchConfigUITheme:
    @pytest.mark.asyncio
    async def test_patch_ui_theme_to_light(self, client):
        resp = await client.patch("/config", json={"ui_theme": "light"})
        assert resp.status_code == 200
        assert resp.json()["ui_theme"] == "light"

    @pytest.mark.asyncio
    async def test_patch_ui_theme_to_dark(self, client):
        resp = await client.patch("/config", json={"ui_theme": "dark"})
        assert resp.status_code == 200
        assert resp.json()["ui_theme"] == "dark"

    @pytest.mark.asyncio
    async def test_patch_ui_theme_persists(self, client):
        await client.patch("/config", json={"ui_theme": "light"})
        resp = await client.get("/config")
        assert resp.json()["ui_theme"] == "light"

    @pytest.mark.asyncio
    async def test_patch_invalid_ui_theme_returns_422(self, client):
        resp = await client.patch("/config", json={"ui_theme": "neon"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_patch_ui_theme_leaves_other_fields_unchanged(self, client):
        resp = await client.patch("/config", json={"ui_theme": "light"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ui_theme"] == "light"
        assert data["llm_provider"] == "anthropic"
