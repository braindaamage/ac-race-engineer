"""FastAPI app factory with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI

from ac_engineer.storage.db import init_db
from api.jobs.manager import JobManager
from api.watcher.observer import SessionWatcher
from api.watcher.scanner import scan_sessions_dir

logger = logging.getLogger(__name__)

DEFAULT_SESSIONS_DIR = Path.home() / "Documents" / "ac-race-engineer" / "sessions"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ac_engineer.db"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.job_manager = JobManager()
    app.state.active_processing_jobs: dict[str, str] = {}
    app.state.active_engineer_jobs: dict[str, str] = {}

    db_path = getattr(app.state, "db_path", DEFAULT_DB_PATH)
    sessions_dir = getattr(app.state, "sessions_dir", DEFAULT_SESSIONS_DIR)

    init_db(db_path)

    # Initial scan to catch sessions missed while server was down
    try:
        result = scan_sessions_dir(sessions_dir, db_path)
        if result.discovered > 0:
            logger.info("Initial scan discovered %d new sessions", result.discovered)
    except Exception:
        logger.exception("Initial session scan failed")

    # Start file watcher
    watcher = SessionWatcher()
    try:
        watcher.start(sessions_dir, db_path)
    except Exception:
        logger.exception("Failed to start session watcher")
    app.state.session_watcher = watcher

    yield

    watcher.stop()
    await app.state.job_manager.cancel_all()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from fastapi.middleware.cors import CORSMiddleware

    from api.routes.analysis import router as analysis_router
    from api.routes.engineer import router as engineer_router
    from api.routes.health import router as health_router
    from api.routes.jobs import router as jobs_router
    from api.routes.sessions import router as sessions_router
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
    app.include_router(sessions_router)
    app.include_router(analysis_router, prefix="/sessions")
    app.include_router(engineer_router, prefix="/sessions")
    app.include_router(ws_jobs_router)
    register_error_handlers(app)

    return app
