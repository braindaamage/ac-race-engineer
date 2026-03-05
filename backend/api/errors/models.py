"""Error response models for uniform API error envelope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Machine-readable error information."""

    type: str
    message: str
    detail: Any = None


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by all API error handlers."""

    error: ErrorDetail
