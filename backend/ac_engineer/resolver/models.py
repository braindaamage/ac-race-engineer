"""Pydantic v2 models for the parameter resolver."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel

from ac_engineer.engineer.models import ParameterRange


class ResolutionTier(IntEnum):
    """Identifies which resolution strategy produced the parameter data."""

    OPEN_DATA = 1
    ACD_ARCHIVE = 2
    SESSION_FALLBACK = 3


class ResolvedParameters(BaseModel):
    """Outcome of parameter resolution for a single car."""

    car_name: str
    tier: ResolutionTier
    parameters: dict[str, ParameterRange]
    has_defaults: bool
    resolved_at: str


class CarStatus(BaseModel):
    """Presentation model for car data management view."""

    car_name: str
    status: str
    tier: int | None = None
    has_defaults: bool | None = None
    resolved_at: str | None = None
