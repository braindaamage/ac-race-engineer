"""Tests for /cars API endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
import httpx

from ac_engineer.resolver.models import CarStatus, ResolvedParameters, ResolutionTier
from ac_engineer.engineer.models import ParameterRange
from api.main import create_app


@pytest.fixture
def app(tmp_path: Path):
    a = create_app()
    # Lifespan doesn't run with AsyncClient, so set state manually
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
    """Create a mock config with defaults."""
    from unittest.mock import MagicMock
    cfg = MagicMock()
    cfg.ac_install_path = kwargs.get("ac_install_path", Path("/fake/ac"))
    return cfg


def _sample_car_statuses():
    return [
        CarStatus(car_name="car_a", status="resolved", tier=1, has_defaults=True, resolved_at="2026-03-08T14:30:00+00:00"),
        CarStatus(car_name="car_b", status="unresolved"),
    ]


def _sample_resolved():
    return ResolvedParameters(
        car_name="car_a",
        tier=ResolutionTier.OPEN_DATA,
        parameters={
            "CAMBER_LF": ParameterRange(
                section="CAMBER_LF", parameter="VALUE",
                min_value=-4.0, max_value=0.0, step=0.1, default_value=-3.0,
            ),
        },
        has_defaults=True,
        resolved_at="2026-03-08T14:30:00+00:00",
    )


class TestGetCars:
    @pytest.mark.anyio
    async def test_returns_car_list(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.read_config", return_value=_mock_config()), \
             patch("api.routes.cars.list_cars", return_value=_sample_car_statuses()):
            resp = await client.get("/cars")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["cars"][0]["car_name"] == "car_a"
        assert data["cars"][0]["status"] == "resolved"
        assert data["cars"][1]["status"] == "unresolved"

    @pytest.mark.anyio
    async def test_returns_400_when_path_not_configured(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.read_config", return_value=_mock_config(ac_install_path=None)), \
             patch("api.routes.cars.list_cars", side_effect=ValueError("path not configured")):
            resp = await client.get("/cars")
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["type"] == "ac_path_not_configured"


class TestGetCarParameters:
    @pytest.mark.anyio
    async def test_returns_cached_parameters(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.get_cached_parameters", return_value=_sample_resolved()):
            resp = await client.get("/cars/car_a/parameters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["car_name"] == "car_a"
        assert "CAMBER_LF" in data["parameters"]

    @pytest.mark.anyio
    async def test_returns_404_when_not_cached(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.get_cached_parameters", return_value=None):
            resp = await client.get("/cars/unknown_car/parameters")
        assert resp.status_code == 404
        assert resp.json()["error"]["type"] == "not_cached"


class TestDeleteCarCache:
    @pytest.mark.anyio
    async def test_returns_200_on_success(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.invalidate_cache", return_value=True):
            resp = await client.delete("/cars/car_a/cache")
        assert resp.status_code == 200
        assert resp.json()["invalidated"] is True

    @pytest.mark.anyio
    async def test_returns_404_when_not_cached(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.invalidate_cache", return_value=False):
            resp = await client.delete("/cars/car_b/cache")
        assert resp.status_code == 404


class TestDeleteAllCaches:
    @pytest.mark.anyio
    async def test_returns_count(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.invalidate_all_caches", return_value=5):
            resp = await client.delete("/cars/cache")
        assert resp.status_code == 200
        assert resp.json()["invalidated_count"] == 5

    @pytest.mark.anyio
    async def test_cache_route_not_treated_as_car_name(self, client: httpx.AsyncClient) -> None:
        """Verify DELETE /cars/cache is matched before DELETE /cars/{car_name}/cache."""
        with patch("api.routes.cars.invalidate_all_caches", return_value=0):
            resp = await client.delete("/cars/cache")
        # Should NOT be 404 (which would mean "cache" was treated as car_name)
        assert resp.status_code == 200


class TestGetCarBadge:
    @pytest.mark.anyio
    async def test_returns_image_when_exists(self, client: httpx.AsyncClient, tmp_path: Path) -> None:
        badge = tmp_path / "ks_ferrari" / "ui" / "badge.png"
        badge.parent.mkdir(parents=True)
        # Write minimal valid PNG
        import base64
        png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        badge.write_bytes(png_data)
        with patch("api.routes.cars.read_config") as mock_cfg:
            mock_cfg.return_value = _mock_config()
            mock_cfg.return_value.ac_cars_path = tmp_path
            with patch("api.routes.cars.car_badge_path", return_value=badge):
                resp = await client.get("/cars/ks_ferrari/badge")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert "max-age=86400" in resp.headers.get("cache-control", "")

    @pytest.mark.anyio
    async def test_returns_404_when_missing(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.read_config", return_value=_mock_config()), \
             patch("api.routes.cars.car_badge_path", return_value=None):
            resp = await client.get("/cars/ks_ferrari/badge")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_rejects_path_traversal(self, client: httpx.AsyncClient) -> None:
        with patch("api.routes.cars.read_config", return_value=_mock_config()):
            resp = await client.get("/cars/..%2F..%2Fetc/badge")
        # Path traversal results in validation error (400) or not found (404)
        assert resp.status_code in (400, 404)
