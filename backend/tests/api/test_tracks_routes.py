"""Tests for /tracks API endpoints."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
import httpx

from api.main import create_app


@pytest.fixture
def app(tmp_path: Path):
    a = create_app()
    a.state.db_path = tmp_path / "test.db"
    a.state.config_path = tmp_path / "config.json"
    return a


@pytest_asyncio.fixture
async def client(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


def _mock_config(**kwargs):
    cfg = MagicMock()
    cfg.ac_install_path = kwargs.get("ac_install_path", Path("/fake/ac"))
    cfg.ac_tracks_path = kwargs.get("ac_tracks_path", Path("/fake/ac/content/tracks"))
    return cfg


def _write_preview(tmp_path: Path, track: str, config: str = "") -> Path:
    """Create a minimal preview.png for testing."""
    if config:
        preview = tmp_path / track / "ui" / f"layout_{config}" / "preview.png"
    else:
        preview = tmp_path / track / "ui" / "preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    preview.write_bytes(png_data)
    return preview


class TestGetTrackPreview:
    @pytest.mark.anyio
    async def test_returns_image_base_layout(self, client, tmp_path) -> None:
        preview = _write_preview(tmp_path, "ks_monza")
        with patch("api.routes.tracks.read_config") as mock_cfg:
            mock_cfg.return_value = _mock_config(ac_tracks_path=tmp_path)
            with patch("api.routes.tracks.track_preview_path", return_value=preview):
                resp = await client.get("/tracks/ks_monza/preview")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert "max-age=86400" in resp.headers.get("cache-control", "")

    @pytest.mark.anyio
    async def test_returns_image_with_config(self, client, tmp_path) -> None:
        preview = _write_preview(tmp_path, "ks_nurburgring", "gp")
        with patch("api.routes.tracks.read_config") as mock_cfg:
            mock_cfg.return_value = _mock_config(ac_tracks_path=tmp_path)
            with patch("api.routes.tracks.track_preview_path", return_value=preview):
                resp = await client.get("/tracks/ks_nurburgring/preview", params={"config": "gp"})
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_returns_404_when_missing(self, client) -> None:
        with patch("api.routes.tracks.read_config", return_value=_mock_config()), \
             patch("api.routes.tracks.track_preview_path", return_value=None):
            resp = await client.get("/tracks/ks_monza/preview")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_rejects_path_traversal(self, client) -> None:
        with patch("api.routes.tracks.read_config", return_value=_mock_config()):
            resp = await client.get("/tracks/..%2F..%2Fetc/preview")
        # Path traversal results in validation error (400) or not found (404)
        assert resp.status_code in (400, 404)
