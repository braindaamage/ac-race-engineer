"""Storage Pydantic v2 models."""

from __future__ import annotations

from pydantic import BaseModel, Field

VALID_SESSION_STATES = ("discovered", "parsed", "analyzed", "engineered")


class SessionRecord(BaseModel):
    """Index record for an analyzed telemetry session."""

    session_id: str = Field(..., min_length=1)
    car: str = Field(..., min_length=1)
    track: str = Field(..., min_length=1)
    session_date: str = Field(..., min_length=1)
    lap_count: int = Field(..., ge=0)
    best_lap_time: float | None = Field(default=None, ge=0)
    state: str = Field(default="discovered")
    session_type: str | None = Field(default=None)
    csv_path: str | None = Field(default=None)
    meta_path: str | None = Field(default=None)


class SyncResult(BaseModel):
    """Result of a session directory scan."""

    discovered: int = 0
    already_known: int = 0
    incomplete: int = 0


class SetupChange(BaseModel):
    """A single parameter modification within a recommendation."""

    change_id: str = ""
    recommendation_id: str = ""
    section: str = Field(..., min_length=1)
    parameter: str = Field(..., min_length=1)
    old_value: str
    new_value: str
    reasoning: str


class Recommendation(BaseModel):
    """A setup change suggestion from the AI engineer."""

    recommendation_id: str = ""
    session_id: str = ""
    status: str = "proposed"
    summary: str = ""
    created_at: str = ""
    changes: list[SetupChange] = Field(default_factory=list)


class Message(BaseModel):
    """A conversation turn between user and AI engineer."""

    message_id: str = ""
    session_id: str = ""
    role: str = ""
    content: str = ""
    created_at: str = ""
