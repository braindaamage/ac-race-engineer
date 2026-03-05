"""Engineer API package — pipeline, serializers, cache."""

from api.engineer.cache import load_engineer_response, save_engineer_response
from api.engineer.pipeline import make_chat_job, make_engineer_job
from api.engineer.serializers import (
    ApplyRequest,
    ApplyResponse,
    ChatJobResponse,
    ChatRequest,
    ClearMessagesResponse,
    DriverFeedbackDetail,
    EngineerJobResponse,
    MessageListResponse,
    MessageResponse,
    RecommendationDetailResponse,
    RecommendationListResponse,
    RecommendationSummary,
    SetupChangeDetail,
)

__all__ = [
    # Pipeline
    "make_engineer_job",
    "make_chat_job",
    # Cache
    "save_engineer_response",
    "load_engineer_response",
    # Serializers
    "EngineerJobResponse",
    "RecommendationSummary",
    "RecommendationListResponse",
    "SetupChangeDetail",
    "DriverFeedbackDetail",
    "RecommendationDetailResponse",
    "ApplyRequest",
    "ApplyResponse",
    "ChatRequest",
    "ChatJobResponse",
    "MessageResponse",
    "MessageListResponse",
    "ClearMessagesResponse",
]
