"""Storage Pydantic v2 models."""

from __future__ import annotations

from typing import Literal

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


VALID_DOMAINS = ("balance", "tyre", "aero", "technique")


class ToolCallDetail(BaseModel):
    """A single tool invocation within an agent execution."""

    detail_id: str = ""
    usage_id: str = ""
    tool_name: str = Field(..., min_length=1)
    token_count: int = Field(..., ge=0)
    called_at: str = ""


class AgentUsage(BaseModel):
    """A specialist agent execution within an engineer recommendation."""

    usage_id: str = ""
    recommendation_id: str = ""
    domain: Literal["balance", "tyre", "aero", "technique"]
    model: str = Field(..., min_length=1)
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    tool_call_count: int = Field(..., ge=0)
    turn_count: int = Field(..., ge=0)
    duration_ms: int = Field(..., ge=0)
    created_at: str = ""
    tool_calls: list[ToolCallDetail] = Field(default_factory=list)
