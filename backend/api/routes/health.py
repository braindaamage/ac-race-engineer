"""Health check endpoint."""

from pydantic import BaseModel
from fastapi import APIRouter

import api


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=api.__version__)
