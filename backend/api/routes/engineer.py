"""Engineer endpoints — run AI engineer, recommendations, chat."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request


from ac_engineer.config.io import read_config
from ac_engineer.engineer.agents import apply_recommendation
from ac_engineer.storage.messages import clear_messages, get_messages, save_message
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.recommendations import get_recommendations
from ac_engineer.storage.sessions import get_session

from api.analysis.cache import get_cache_dir
from api.engineer.cache import load_engineer_response
from api.engineer.pipeline import make_chat_job, make_engineer_job
from ac_engineer.storage.usage import get_llm_events

from api.engineer.serializers import (
    AgentUsageDetail,
    ApplyRequest,
    ApplyResponse,
    ChatJobResponse,
    ChatRequest,
    ClearMessagesResponse,
    DriverFeedbackDetail,
    EngineerJobResponse,
    MessageListResponse,
    MessageResponse,
    MessageUsageResponse,
    RecommendationDetailResponse,
    RecommendationListResponse,
    RecommendationSummary,
    RecommendationUsageResponse,
    SetupChangeDetail,
    ToolCallInfo,
    TraceResponse,
    UsageTotals,
)
from api.jobs.worker import run_job

router = APIRouter()


def _require_analyzed_session(db_path, session_id: str) -> SessionRecord:
    """Guard: session must exist and be in analyzed/engineered state."""
    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    if session.state not in ("analyzed", "engineered"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Session has not been analyzed yet. "
                f"Current state: {session.state}. Process the session first."
            ),
        )
    return session


def _resolve_setup_path(
    session: SessionRecord,
    sessions_dir: str | Path,
    config,
) -> Path:
    """Auto-resolve setup file path from session metadata and config.

    Reads the .meta.json, finds the last setup_history entry with a filename,
    and constructs the full path: {config.setups_path}/{car}/{track}/{filename}.
    """
    if not config.setups_path:
        raise HTTPException(
            status_code=400,
            detail="No setups_path configured. Set it in Settings.",
        )

    # Load meta.json to get setup_history
    meta_path = session.meta_path
    if not meta_path or not Path(meta_path).is_file():
        raise HTTPException(
            status_code=400,
            detail="No setup file found in session history. Please specify a setup_path.",
        )

    try:
        meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=400,
            detail="No setup file found in session history. Please specify a setup_path.",
        )

    setup_history = meta.get("setup_history", [])

    # Find last entry with a non-null filename
    filename = None
    for entry in reversed(setup_history):
        fn = entry.get("filename")
        if fn:
            filename = fn
            break

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No setup file found in session history. Please specify a setup_path.",
        )

    track = meta.get("track_name", session.track)
    return Path(config.setups_path) / session.car / track / filename


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/engineer
# ---------------------------------------------------------------------------


@router.post("/{session_id}/engineer", response_model=EngineerJobResponse, status_code=202)
async def run_engineer(request: Request, session_id: str) -> EngineerJobResponse:
    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir
    manager = request.app.state.job_manager
    active_jobs: dict[str, str] = request.app.state.active_engineer_jobs

    _require_analyzed_session(db_path, session_id)

    if session_id in active_jobs:
        raise HTTPException(
            status_code=409,
            detail=f"Engineer job already running for session: {session_id}",
        )

    config_path = request.app.state.config_path
    config = read_config(config_path)

    job = manager.create_job("run_engineer")
    active_jobs[session_id] = job.job_id

    pipeline = make_engineer_job(
        session_id=session_id,
        sessions_dir=sessions_dir,
        db_path=db_path,
        config=config,
        active_jobs=active_jobs,
    )

    task = asyncio.create_task(run_job(manager, job.job_id, pipeline))
    manager.register_task(job.job_id, task)

    return EngineerJobResponse(job_id=job.job_id, session_id=session_id)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations
# ---------------------------------------------------------------------------


@router.get("/{session_id}/recommendations", response_model=RecommendationListResponse)
async def list_recommendations(request: Request, session_id: str) -> RecommendationListResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recs = get_recommendations(db_path, session_id)
    items = [
        RecommendationSummary(
            recommendation_id=r.recommendation_id,
            session_id=r.session_id,
            status=r.status,
            summary=r.summary,
            change_count=len(r.changes),
            created_at=r.created_at,
        )
        for r in recs
    ]
    return RecommendationListResponse(session_id=session_id, recommendations=items)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations/{recommendation_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/recommendations/{recommendation_id}",
    response_model=RecommendationDetailResponse,
)
async def get_recommendation_detail(
    request: Request, session_id: str, recommendation_id: str
) -> RecommendationDetailResponse:
    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recs = get_recommendations(db_path, session_id)
    rec = next((r for r in recs if r.recommendation_id == recommendation_id), None)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    # Try loading cached EngineerResponse for full detail
    cache_dir = get_cache_dir(sessions_dir, session_id)
    cached = load_engineer_response(cache_dir, recommendation_id)

    if cached is not None:
        setup_changes = [
            SetupChangeDetail(
                section=c.section,
                parameter=c.parameter,
                old_value=str(c.value_before) if c.value_before is not None else "",
                new_value=str(c.value_after),
                reasoning=c.reasoning,
                expected_effect=c.expected_effect,
                confidence=c.confidence,
                storage_value_before=c.storage_value_before,
                storage_value_after=c.storage_value_after,
                storage_convention=c.storage_convention,
            )
            for c in cached.setup_changes
        ]
        driver_feedback = [
            DriverFeedbackDetail(
                area=f.area,
                observation=f.observation,
                suggestion=f.suggestion,
                corners_affected=f.corners_affected,
                severity=f.severity,
            )
            for f in cached.driver_feedback
        ]
        return RecommendationDetailResponse(
            recommendation_id=rec.recommendation_id,
            session_id=rec.session_id,
            status=rec.status,
            summary=rec.summary,
            explanation=rec.explanation or cached.explanation,
            confidence=cached.confidence,
            signals_addressed=cached.signals_addressed,
            setup_changes=setup_changes,
            driver_feedback=driver_feedback,
            created_at=rec.created_at,
        )

    # Fallback: SQLite-only data (no cached EngineerResponse)
    setup_changes = [
        SetupChangeDetail(
            section=c.section,
            parameter=c.parameter,
            old_value=c.old_value,
            new_value=c.new_value,
            reasoning=c.reasoning,
        )
        for c in rec.changes
    ]
    return RecommendationDetailResponse(
        recommendation_id=rec.recommendation_id,
        session_id=rec.session_id,
        status=rec.status,
        summary=rec.summary,
        explanation=rec.explanation,
        setup_changes=setup_changes,
        created_at=rec.created_at,
    )


# ---------------------------------------------------------------------------
# Usage response helper
# ---------------------------------------------------------------------------


def _compute_usage_response(usage_records):
    """Compute UsageTotals and AgentUsageDetail list from LlmEvent records."""
    total_input = sum(u.input_tokens for u in usage_records)
    total_output = sum(u.output_tokens for u in usage_records)
    total_cache_read = sum(u.cache_read_tokens for u in usage_records)
    total_cache_write = sum(u.cache_write_tokens for u in usage_records)
    total_tool_calls = sum(u.tool_call_count for u in usage_records)

    totals = UsageTotals(
        input_tokens=total_input,
        output_tokens=total_output,
        total_tokens=total_input + total_output,
        cache_read_tokens=total_cache_read,
        cache_write_tokens=total_cache_write,
        tool_call_count=total_tool_calls,
        agent_count=len(usage_records),
    )

    agents = [
        AgentUsageDetail(
            domain=u.agent_name,
            model=u.model,
            input_tokens=u.input_tokens,
            output_tokens=u.output_tokens,
            cache_read_tokens=u.cache_read_tokens,
            cache_write_tokens=u.cache_write_tokens,
            tool_call_count=u.tool_call_count,
            turn_count=u.request_count,
            duration_ms=u.duration_ms,
            tool_calls=[
                ToolCallInfo(tool_name=tc.tool_name, token_count=tc.response_tokens)
                for tc in u.tool_calls
            ],
        )
        for u in usage_records
    ]

    return totals, agents


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations/{recommendation_id}/usage
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/recommendations/{recommendation_id}/usage",
    response_model=RecommendationUsageResponse,
)
async def get_recommendation_usage(
    request: Request, session_id: str, recommendation_id: str
) -> RecommendationUsageResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recs = get_recommendations(db_path, session_id)
    rec = next((r for r in recs if r.recommendation_id == recommendation_id), None)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    usage_records = get_llm_events(db_path, "recommendation", recommendation_id)

    totals, agents = _compute_usage_response(usage_records)

    return RecommendationUsageResponse(
        recommendation_id=recommendation_id,
        totals=totals,
        agents=agents,
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations/{recommendation_id}/trace
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/recommendations/{recommendation_id}/trace",
    response_model=TraceResponse,
)
async def get_recommendation_trace(
    request: Request, session_id: str, recommendation_id: str
) -> TraceResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recs = get_recommendations(db_path, session_id)
    rec = next((r for r in recs if r.recommendation_id == recommendation_id), None)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    from ac_engineer.engineer.trace import read_trace
    from api.paths import get_traces_dir

    content = read_trace(get_traces_dir(), "rec", recommendation_id)
    return TraceResponse(
        available=content is not None,
        content=content,
        trace_type="recommendation",
        id=recommendation_id,
    )


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/recommendations/{recommendation_id}/apply
# ---------------------------------------------------------------------------


@router.post(
    "/{session_id}/recommendations/{recommendation_id}/apply",
    response_model=ApplyResponse,
)
async def apply_recommendation_endpoint(
    request: Request,
    session_id: str,
    recommendation_id: str,
    body: ApplyRequest,
) -> ApplyResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    recs = get_recommendations(db_path, session_id)
    rec = next((r for r in recs if r.recommendation_id == recommendation_id), None)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    if rec.status == "applied":
        raise HTTPException(
            status_code=409,
            detail=f"Recommendation already applied: {recommendation_id}",
        )

    config_path = request.app.state.config_path
    config = read_config(config_path)

    # Resolve setup_path: use provided value or auto-resolve from session metadata
    if body.setup_path.strip():
        setup_path = Path(body.setup_path)
    else:
        setup_path = _resolve_setup_path(
            session=session,
            sessions_dir=request.app.state.sessions_dir,
            config=config,
        )

    if not setup_path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Setup file not found: {setup_path}",
        )

    outcomes = await apply_recommendation(
        recommendation_id=recommendation_id,
        setup_path=setup_path,
        db_path=Path(db_path),
        ac_install_path=config.ac_install_path,
        car_name=session.car,
    )

    # Find backup path (the backup is created by apply_recommendation)
    backup_candidates = sorted(
        setup_path.parent.glob(f"{setup_path.stem}_*{setup_path.suffix}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    backup_path = str(backup_candidates[0]) if backup_candidates else ""

    return ApplyResponse(
        recommendation_id=recommendation_id,
        status="applied",
        backup_path=backup_path,
        changes_applied=len(outcomes),
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages/{message_id}/trace
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/messages/{message_id}/trace",
    response_model=TraceResponse,
)
async def get_message_trace(
    request: Request, session_id: str, message_id: str
) -> TraceResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    msgs = get_messages(db_path, session_id)
    msg = next((m for m in msgs if m.message_id == message_id), None)
    if msg is None:
        raise HTTPException(
            status_code=404,
            detail=f"Message not found: {message_id}",
        )

    from ac_engineer.engineer.trace import read_trace
    from api.paths import get_traces_dir

    content = read_trace(get_traces_dir(), "msg", message_id)
    return TraceResponse(
        available=content is not None,
        content=content,
        trace_type="message",
        id=message_id,
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages/{message_id}/usage
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/messages/{message_id}/usage",
    response_model=MessageUsageResponse,
)
async def get_message_usage(
    request: Request, session_id: str, message_id: str
) -> MessageUsageResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Validate message exists in this session
    msgs = get_messages(db_path, session_id)
    msg = next((m for m in msgs if m.message_id == message_id), None)
    if msg is None:
        raise HTTPException(
            status_code=404,
            detail=f"Message not found: {message_id}",
        )

    usage_records = get_llm_events(db_path, "message", message_id)
    totals, agents = _compute_usage_response(usage_records)

    return MessageUsageResponse(
        message_id=message_id,
        totals=totals,
        agents=agents,
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(request: Request, session_id: str) -> MessageListResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    msgs = get_messages(db_path, session_id)
    items = [
        MessageResponse(
            message_id=m.message_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in msgs
    ]
    return MessageListResponse(session_id=session_id, messages=items)


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


@router.post("/{session_id}/messages", response_model=ChatJobResponse, status_code=202)
async def send_message(
    request: Request, session_id: str, body: ChatRequest
) -> ChatJobResponse:
    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir
    manager = request.app.state.job_manager

    _require_analyzed_session(db_path, session_id)

    # Save user message first
    user_msg = save_message(db_path, session_id, "user", body.content)

    config_path = request.app.state.config_path
    config = read_config(config_path)

    job = manager.create_job("chat_response")

    chat_pipeline = make_chat_job(
        session_id=session_id,
        message_id=user_msg.message_id,
        user_content=body.content,
        sessions_dir=sessions_dir,
        db_path=db_path,
        config=config,
    )

    task = asyncio.create_task(run_job(manager, job.job_id, chat_pipeline))
    manager.register_task(job.job_id, task)

    return ChatJobResponse(job_id=job.job_id, message_id=user_msg.message_id)


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


@router.delete("/{session_id}/messages", response_model=ClearMessagesResponse)
async def delete_messages(request: Request, session_id: str) -> ClearMessagesResponse:
    db_path = request.app.state.db_path

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    count = clear_messages(db_path, session_id)
    return ClearMessagesResponse(session_id=session_id, deleted_count=count)
