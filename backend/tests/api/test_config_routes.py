"""Tests for config route endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
        assert data["api_key"] == ""
        assert data["onboarding_completed"] is False

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

    @pytest.mark.asyncio
    async def test_patch_api_key_saves_and_returns_masked(self, client):
        resp = await client.patch("/config", json={"api_key": "sk-ant-api03-abcdef1234567890"})
        assert resp.status_code == 200
        data = resp.json()
        # Masked: first 4 + **** + last 4
        assert data["api_key"] == "sk-a****7890"

    @pytest.mark.asyncio
    async def test_patch_api_key_read_back_still_masked(self, client):
        await client.patch("/config", json={"api_key": "sk-ant-api03-abcdef1234567890"})
        resp = await client.get("/config")
        data = resp.json()
        assert data["api_key"] == "sk-a****7890"

    @pytest.mark.asyncio
    async def test_patch_onboarding_completed_true(self, client):
        resp = await client.patch("/config", json={"onboarding_completed": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["onboarding_completed"] is True

    @pytest.mark.asyncio
    async def test_onboarding_completed_default_false(self, client):
        resp = await client.get("/config")
        data = resp.json()
        assert data["onboarding_completed"] is False


# ---------------------------------------------------------------------------
# GET /config/validate
# ---------------------------------------------------------------------------


class TestValidateConfig:
    @pytest.mark.asyncio
    async def test_validate_all_valid(self, client, config_path, tmp_path):
        ac_dir = tmp_path / "ac_install"
        ac_dir.mkdir()
        (ac_dir / "content").mkdir()
        (ac_dir / "content" / "cars").mkdir()
        (ac_dir / "content" / "tracks").mkdir()
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
        assert data["ac_path"]["status"] == "valid"
        assert data["setups_path"]["status"] == "valid"
        assert data["llm_provider"]["status"] == "valid"
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
        assert data["ac_path"]["status"] == "empty"
        assert data["setups_path"]["status"] == "valid"
        assert data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_missing_setups_path(self, client, config_path, tmp_path):
        ac_dir = tmp_path / "ac_install"
        ac_dir.mkdir()
        (ac_dir / "content").mkdir()
        (ac_dir / "content" / "cars").mkdir()
        (ac_dir / "content" / "tracks").mkdir()
        config_path.write_text(
            json.dumps({
                "ac_install_path": str(ac_dir),
                "llm_provider": "anthropic",
            }),
            encoding="utf-8",
        )
        resp = await client.get("/config/validate")
        data = resp.json()
        assert data["ac_path"]["status"] == "valid"
        assert data["setups_path"]["status"] == "empty"
        assert data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_empty_config(self, client):
        resp = await client.get("/config/validate")
        data = resp.json()
        assert data["ac_path"]["status"] == "empty"
        assert data["setups_path"]["status"] == "empty"
        assert data["llm_provider"]["status"] == "valid"  # defaults to "anthropic"
        assert data["is_valid"] is False
        assert data["onboarding_completed"] is False


# ---------------------------------------------------------------------------
# POST /config/validate-path
# ---------------------------------------------------------------------------


class TestValidatePath:
    @pytest.mark.asyncio
    async def test_ac_install_empty(self, client):
        resp = await client.post("/config/validate-path", json={"path": "", "path_type": "ac_install"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "empty"

    @pytest.mark.asyncio
    async def test_ac_install_not_found(self, client, tmp_path):
        resp = await client.post("/config/validate-path", json={
            "path": str(tmp_path / "nonexistent"),
            "path_type": "ac_install",
        })
        data = resp.json()
        assert data["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_ac_install_no_content(self, client, tmp_path):
        ac_dir = tmp_path / "ac"
        ac_dir.mkdir()
        resp = await client.post("/config/validate-path", json={
            "path": str(ac_dir),
            "path_type": "ac_install",
        })
        data = resp.json()
        assert data["status"] == "warning"
        assert "content" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_ac_install_partial_content(self, client, tmp_path):
        ac_dir = tmp_path / "ac"
        ac_dir.mkdir()
        (ac_dir / "content").mkdir()
        resp = await client.post("/config/validate-path", json={
            "path": str(ac_dir),
            "path_type": "ac_install",
        })
        data = resp.json()
        assert data["status"] == "warning"

    @pytest.mark.asyncio
    async def test_ac_install_valid(self, client, tmp_path):
        ac_dir = tmp_path / "ac"
        ac_dir.mkdir()
        (ac_dir / "content").mkdir()
        (ac_dir / "content" / "cars").mkdir()
        (ac_dir / "content" / "tracks").mkdir()
        resp = await client.post("/config/validate-path", json={
            "path": str(ac_dir),
            "path_type": "ac_install",
        })
        data = resp.json()
        assert data["status"] == "valid"
        assert data["message"] == "Valid Assetto Corsa installation found."

    @pytest.mark.asyncio
    async def test_setups_empty(self, client):
        resp = await client.post("/config/validate-path", json={"path": "", "path_type": "setups"})
        data = resp.json()
        assert data["status"] == "empty"

    @pytest.mark.asyncio
    async def test_setups_not_found(self, client, tmp_path):
        resp = await client.post("/config/validate-path", json={
            "path": str(tmp_path / "nonexistent"),
            "path_type": "setups",
        })
        data = resp.json()
        assert data["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_setups_valid(self, client, tmp_path):
        setups_dir = tmp_path / "setups"
        setups_dir.mkdir()
        resp = await client.post("/config/validate-path", json={
            "path": str(setups_dir),
            "path_type": "setups",
        })
        data = resp.json()
        assert data["status"] == "valid"
        assert data["message"] == "Setups folder found."

    @pytest.mark.asyncio
    async def test_invalid_path_type(self, client):
        resp = await client.post("/config/validate-path", json={"path": "/tmp", "path_type": "unknown"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /config/validate-api-key
# ---------------------------------------------------------------------------


def _mock_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code=status_code, request=httpx.Request("GET", "https://test"))


class TestValidateApiKey:
    @pytest.mark.asyncio
    async def test_valid_key_returns_valid_true(self, client):
        mock_resp = _mock_response(200)
        with patch("api.routes.config.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = await client.post("/config/validate-api-key", json={
                "provider": "anthropic",
                "api_key": "sk-ant-test",
            })
            data = resp.json()
            assert data["valid"] is True
            assert "Anthropic" in data["message"]

    @pytest.mark.asyncio
    async def test_401_returns_invalid_auth(self, client):
        mock_resp = _mock_response(401)
        with patch("api.routes.config.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = await client.post("/config/validate-api-key", json={
                "provider": "openai",
                "api_key": "sk-bad-key",
            })
            data = resp.json()
            assert data["valid"] is False
            assert "Invalid API key" in data["message"]

    @pytest.mark.asyncio
    async def test_timeout_returns_network_error(self, client):
        with patch("api.routes.config.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = await client.post("/config/validate-api-key", json={
                "provider": "anthropic",
                "api_key": "sk-ant-test",
            })
            data = resp.json()
            assert data["valid"] is False
            assert "Could not reach" in data["message"]

    @pytest.mark.asyncio
    async def test_429_returns_rate_limit(self, client):
        mock_resp = _mock_response(429)
        with patch("api.routes.config.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = await client.post("/config/validate-api-key", json={
                "provider": "gemini",
                "api_key": "AIza-test",
            })
            data = resp.json()
            assert data["valid"] is False
            assert "Rate limited" in data["message"]

    @pytest.mark.asyncio
    async def test_invalid_provider(self, client):
        resp = await client.post("/config/validate-api-key", json={
            "provider": "bedrock",
            "api_key": "test",
        })
        data = resp.json()
        assert data["valid"] is False
        assert "Unknown provider" in data["message"]
