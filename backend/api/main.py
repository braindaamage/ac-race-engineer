"""FastAPI app factory with lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from api.jobs.manager import JobManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.job_manager = JobManager()
    yield
    await app.state.job_manager.cancel_all()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from fastapi.middleware.cors import CORSMiddleware

    from api.routes.health import router as health_router
    from api.routes.jobs import router as jobs_router
    from api.ws.jobs import router as ws_jobs_router
    from api.errors.handlers import register_error_handlers

    app = FastAPI(title="AC Race Engineer API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://localhost(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(ws_jobs_router)
    register_error_handlers(app)

    return app
