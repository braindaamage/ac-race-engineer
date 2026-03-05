"""Health check and lifecycle endpoints."""

from pydantic import BaseModel
from fastapi import APIRouter, Request

import api


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class ShutdownResponse(BaseModel):
    """Shutdown response."""

    status: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=api.__version__)


@router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown(request: Request) -> ShutdownResponse:
    server = getattr(request.app.state, "server", None)
    if server is not None:
        server.should_exit = True
    return ShutdownResponse(status="shutting_down")
