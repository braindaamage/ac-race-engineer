"""API response models for engineer endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class EngineerJobResponse(BaseModel):
    """Response for POST /sessions/{session_id}/engineer (202)."""

    job_id: str
    session_id: str


class RecommendationSummary(BaseModel):
    """Item in recommendation list."""

    recommendation_id: str
    session_id: str
    status: str
    summary: str
    change_count: int
    created_at: str


class RecommendationListResponse(BaseModel):
    """Response for GET /sessions/{session_id}/recommendations."""

    session_id: str
    recommendations: list[RecommendationSummary]


class SetupChangeDetail(BaseModel):
    """Rich setup change for recommendation detail."""

    section: str
    parameter: str
    old_value: str
    new_value: str
    reasoning: str
    expected_effect: str = ""
    confidence: str = "medium"


class DriverFeedbackDetail(BaseModel):
    """Driver feedback item."""

    area: str
    observation: str
    suggestion: str
    corners_affected: list[int] = []
    severity: str


class RecommendationDetailResponse(BaseModel):
    """Response for GET /sessions/{session_id}/recommendations/{rec_id}."""

    recommendation_id: str
    session_id: str
    status: str
    summary: str
    explanation: str = ""
    confidence: str = "medium"
    signals_addressed: list[str] = []
    setup_changes: list[SetupChangeDetail] = []
    driver_feedback: list[DriverFeedbackDetail] = []
    created_at: str


class ApplyRequest(BaseModel):
    """Body for POST /recommendations/{rec_id}/apply."""

    setup_path: str


class ApplyResponse(BaseModel):
    """Response for POST /recommendations/{rec_id}/apply."""

    recommendation_id: str
    status: str = "applied"
    backup_path: str
    changes_applied: int


class ChatRequest(BaseModel):
    """Body for POST /messages."""

    content: str


class ChatJobResponse(BaseModel):
    """Response for POST /sessions/{session_id}/messages (202)."""

    job_id: str
    message_id: str


class MessageResponse(BaseModel):
    """Single message in history."""

    message_id: str
    role: str
    content: str
    created_at: str


class MessageListResponse(BaseModel):
    """Response for GET /sessions/{session_id}/messages."""

    session_id: str
    messages: list[MessageResponse]


class ClearMessagesResponse(BaseModel):
    """Response for DELETE /sessions/{session_id}/messages."""

    session_id: str
    deleted_count: int
