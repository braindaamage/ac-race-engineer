"""Shared test fixtures for API tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
import httpx

from api.main import create_app
from api.jobs.manager import JobManager


@pytest.fixture
def app():
    """Create a fresh FastAPI app for each test."""
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP client wired to the test app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


@pytest.fixture
def manager(app) -> JobManager:
    """Return the app's JobManager (initialized during lifespan)."""
    # Lifespan doesn't run with AsyncClient, so set it manually
    mgr = JobManager()
    app.state.job_manager = mgr
    return mgr
