"""Tests for config route endpoints."""

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
    """Config path — file does NOT exist yet (defaults)."""
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
# GET /config
# ---------------------------------------------------------------------------


class TestGetConfig:
    @pytest.mark.asyncio
    async def test_returns_defaults_with_empty_strings(self, client):
        resp = await client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ac_install_path"] == ""
        assert data["setups_path"] == ""
        assert data["llm_provider"] == "anthropic"
        assert data["llm_model"] == ""

    @pytest.mark.asyncio
    async def test_returns_existing_config_values(self, client, config_path):
        config_path.write_text(
            json.dumps({
                "ac_install_path": "C:\\Games\\AC",
                "setups_path": "C:\\Setups",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            }),
            encoding="utf-8",
        )
        resp = await client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ac_install_path"] == "C:\\Games\\AC"
        assert data["setups_path"] == "C:\\Setups"
        assert data["llm_provider"] == "openai"
        assert data["llm_model"] == "gpt-4o"


# ---------------------------------------------------------------------------
# PATCH /config
# ---------------------------------------------------------------------------


class TestPatchConfig:
    @pytest.mark.asyncio
    async def test_patch_single_field_leaves_others_unchanged(self, client):
        resp = await client.patch("/config", json={"llm_provider": "openai"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["llm_provider"] == "openai"
        assert data["ac_install_path"] == ""
        assert data["llm_model"] == ""

    @pytest.mark.asyncio
    async def test_patch_multiple_fields(self, client):
        resp = await client.patch("/config", json={
            "llm_provider": "gemini",
            "llm_model": "gemini-1.5-pro",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["llm_provider"] == "gemini"
        assert data["llm_model"] == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_patch_empty_body_returns_current(self, client):
        resp = await client.patch("/config", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["llm_provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_patch_invalid_llm_provider_returns_422(self, client):
        resp = await client.patch("/config", json={"llm_provider": "bedrock"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_patch_unknown_field_returns_422(self, client):
        resp = await client.patch("/config", json={"unknown_field": "value"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /config/validate
# ---------------------------------------------------------------------------


class TestValidateConfig:
    @pytest.mark.asyncio
    async def test_validate_all_valid(self, client, config_path, tmp_path):
        ac_dir = tmp_path / "ac_install"
        ac_dir.mkdir()
        setups_dir = tmp_path / "setups"
        setups_dir.mkdir()
        config_path.write_text(
            json.dumps({
                "ac_install_path": str(ac_dir),
                "setups_path": str(setups_dir),
                "llm_provider": "anthropic",
            }),
            encoding="utf-8",
        )
        resp = await client.get("/config/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ac_path_valid"] is True
        assert data["setups_path_valid"] is True
        assert data["llm_provider_valid"] is True
        assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_missing_ac_path(self, client, config_path, tmp_path):
        setups_dir = tmp_path / "setups"
        setups_dir.mkdir()
        config_path.write_text(
            json.dumps({
                "setups_path": str(setups_dir),
                "llm_provider": "anthropic",
            }),
            encoding="utf-8",
        )
        resp = await client.get("/config/validate")
        data = resp.json()
        assert data["ac_path_valid"] is False
        assert data["setups_path_valid"] is True
        assert data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_missing_setups_path(self, client, config_path, tmp_path):
        ac_dir = tmp_path / "ac_install"
        ac_dir.mkdir()
        config_path.write_text(
            json.dumps({
                "ac_install_path": str(ac_dir),
                "llm_provider": "anthropic",
            }),
            encoding="utf-8",
        )
        resp = await client.get("/config/validate")
        data = resp.json()
        assert data["ac_path_valid"] is True
        assert data["setups_path_valid"] is False
        assert data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_empty_config(self, client):
        resp = await client.get("/config/validate")
        data = resp.json()
        assert data["ac_path_valid"] is False
        assert data["setups_path_valid"] is False
        assert data["llm_provider_valid"] is True  # defaults to "anthropic"
        assert data["is_valid"] is False
