"""Engineer: session summarizer, setup reader/writer, AI agents."""

from __future__ import annotations

from .agents import (
    DOMAIN_PRIORITY,
    SIGNAL_DOMAINS,
    AgentDeps,
    SpecialistResult,
    analyze_with_engineer,
    apply_recommendation,
    build_model,
    get_model_string,
    route_signals,
)
from .models import (
    ChangeOutcome,
    CornerIssue,
    DriverFeedback,
    EngineerResponse,
    LapSummary,
    ParameterRange,
    SessionSummary,
    SetupChange,
    StintSummary,
    ValidationResult,
)
from .setup_reader import get_parameter_range, read_parameter_ranges
from .setup_writer import apply_changes, create_backup, validate_changes
from .summarizer import summarize_session

__all__ = [
    # Functions — Phase 5.2
    "summarize_session",
    "read_parameter_ranges",
    "get_parameter_range",
    "validate_changes",
    "apply_changes",
    "create_backup",
    # Functions — Phase 5.3
    "analyze_with_engineer",
    "apply_recommendation",
    "route_signals",
    "get_model_string",
    "build_model",
    # Models — Phase 5.2
    "SessionSummary",
    "LapSummary",
    "CornerIssue",
    "StintSummary",
    "ParameterRange",
    "ValidationResult",
    "ChangeOutcome",
    "SetupChange",
    "DriverFeedback",
    "EngineerResponse",
    # Models — Phase 5.3
    "SpecialistResult",
    "AgentDeps",
    # Constants — Phase 5.3
    "SIGNAL_DOMAINS",
    "DOMAIN_PRIORITY",
]
