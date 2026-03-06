"""Analysis endpoints — POST /process + 8 metric GET endpoints."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, Response
from starlette.responses import JSONResponse

from ac_engineer.analyzer.models import AnalyzedSession, ConsistencyMetrics
from ac_engineer.storage.sessions import get_session

from api.analysis.cache import get_cache_dir, load_analyzed_session
from api.analysis.models import (
    ConsistencyResponse,
    CornerDetailResponse,
    CornerListResponse,
    LapDetailResponse,
    LapListResponse,
    LapTelemetryResponse,
    ProcessResponse,
    StintComparisonResponse,
    StintListResponse,
)
from api.analysis.pipeline import make_processing_job
from api.analysis.serializers import (
    aggregate_corners,
    get_corner_by_lap,
    summarize_all_laps,
    telemetry_for_lap,
)
from api.jobs.worker import run_job

router = APIRouter()


async def _get_analyzed_session(request: Request, session_id: str) -> AnalyzedSession:
    """Shared guard: look up session, check state, load cache."""
    db_path = request.app.state.db_path
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

    sessions_dir = request.app.state.sessions_dir
    cache_dir = get_cache_dir(sessions_dir, session_id)
    try:
        return load_analyzed_session(cache_dir)
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=409,
            detail="Cached results are corrupted or missing — re-process the session",
        )


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/process
# ---------------------------------------------------------------------------


@router.post("/{session_id}/process", response_model=ProcessResponse, status_code=202)
async def process_session(request: Request, session_id: str) -> ProcessResponse:
    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir
    manager = request.app.state.job_manager
    active_jobs: dict[str, str] = request.app.state.active_processing_jobs

    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    if session_id in active_jobs:
        raise HTTPException(
            status_code=409,
            detail=f"Processing already in progress for session: {session_id}",
        )

    if not session.csv_path or not session.meta_path:
        raise HTTPException(
            status_code=409,
            detail=f"Session is missing csv_path or meta_path: {session_id}",
        )

    job = manager.create_job("process_session")
    active_jobs[session_id] = job.job_id

    pipeline = make_processing_job(
        session_id=session_id,
        csv_path=session.csv_path,
        meta_path=session.meta_path,
        sessions_dir=sessions_dir,
        db_path=db_path,
        active_jobs=active_jobs,
    )

    task = asyncio.create_task(run_job(manager, job.job_id, pipeline))
    manager.register_task(job.job_id, task)

    return ProcessResponse(job_id=job.job_id, session_id=session_id)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps
# ---------------------------------------------------------------------------


@router.get("/{session_id}/laps", response_model=LapListResponse)
async def list_laps(request: Request, session_id: str) -> LapListResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    laps = summarize_all_laps(analyzed)
    return LapListResponse(session_id=session_id, lap_count=len(laps), laps=laps)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps/{lap_number}
# ---------------------------------------------------------------------------


@router.get("/{session_id}/laps/{lap_number}", response_model=LapDetailResponse)
async def get_lap_detail(request: Request, session_id: str, lap_number: int) -> LapDetailResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    for lap in analyzed.laps:
        if lap.lap_number == lap_number:
            return LapDetailResponse(
                session_id=session_id,
                lap_number=lap.lap_number,
                classification=lap.classification,
                is_invalid=lap.is_invalid,
                metrics=lap.metrics,
                corners=lap.corners,
            )
    raise HTTPException(status_code=404, detail=f"Lap {lap_number} not found in session: {session_id}")


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps/{lap_number}/telemetry
# ---------------------------------------------------------------------------


def _find_parquet(sessions_dir: str | Path, session_id: str) -> Path:
    """Find telemetry.parquet inside the session cache directory."""
    cache_dir = Path(sessions_dir) / session_id
    parquet_files = list(cache_dir.rglob("telemetry.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"telemetry.parquet not found for session: {session_id}")
    return parquet_files[0]


@router.get(
    "/{session_id}/laps/{lap_number}/telemetry",
    response_model=LapTelemetryResponse,
)
async def get_lap_telemetry(
    request: Request,
    session_id: str,
    lap_number: int,
    max_samples: int = Query(default=500, ge=0),
) -> LapTelemetryResponse:
    # Reuse the analyzed-session guard to verify session exists & is analyzed
    await _get_analyzed_session(request, session_id)

    sessions_dir = request.app.state.sessions_dir
    try:
        parquet_path = _find_parquet(sessions_dir, session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Telemetry data not found for session")

    try:
        return await asyncio.to_thread(
            telemetry_for_lap, parquet_path, session_id, lap_number, max_samples,
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Lap {lap_number} not found in session: {session_id}",
        )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/corners
# ---------------------------------------------------------------------------


@router.get("/{session_id}/corners", response_model=CornerListResponse)
async def list_corners(request: Request, session_id: str) -> CornerListResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    corners = aggregate_corners(analyzed)
    return CornerListResponse(session_id=session_id, corner_count=len(corners), corners=corners)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/corners/{corner_number}
# ---------------------------------------------------------------------------


@router.get("/{session_id}/corners/{corner_number}", response_model=CornerDetailResponse)
async def get_corner_detail(request: Request, session_id: str, corner_number: int) -> CornerDetailResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    entries = get_corner_by_lap(analyzed, corner_number)
    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"Corner {corner_number} not found in session: {session_id}",
        )
    return CornerDetailResponse(session_id=session_id, corner_number=corner_number, laps=entries)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/stints
# ---------------------------------------------------------------------------


@router.get("/{session_id}/stints", response_model=StintListResponse)
async def list_stints(request: Request, session_id: str) -> StintListResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    return StintListResponse(
        session_id=session_id,
        stint_count=len(analyzed.stints),
        stints=analyzed.stints,
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/compare
# ---------------------------------------------------------------------------


@router.get("/{session_id}/compare", response_model=StintComparisonResponse)
async def compare_stints(
    request: Request,
    session_id: str,
    stint_a: int = Query(...),
    stint_b: int = Query(...),
) -> StintComparisonResponse:
    analyzed = await _get_analyzed_session(request, session_id)

    # Validate stint indices exist
    stint_indices = {s.stint_index for s in analyzed.stints}
    if stint_a not in stint_indices or stint_b not in stint_indices:
        raise HTTPException(
            status_code=404,
            detail=f"Stint index not found. Available: {sorted(stint_indices)}",
        )

    for comp in analyzed.stint_comparisons:
        if (comp.stint_a_index == stint_a and comp.stint_b_index == stint_b) or \
           (comp.stint_a_index == stint_b and comp.stint_b_index == stint_a):
            return StintComparisonResponse(session_id=session_id, comparison=comp)

    raise HTTPException(
        status_code=404,
        detail=f"No comparison found for stints {stint_a} and {stint_b}",
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/consistency
# ---------------------------------------------------------------------------


@router.get("/{session_id}/consistency", response_model=ConsistencyResponse)
async def get_consistency(request: Request, session_id: str) -> ConsistencyResponse:
    analyzed = await _get_analyzed_session(request, session_id)
    consistency = analyzed.consistency
    if consistency is None:
        consistency = ConsistencyMetrics(
            flying_lap_count=0,
            lap_time_stddev_s=0,
            best_lap_time_s=0,
            worst_lap_time_s=0,
            lap_time_trend_slope=None,
            corner_consistency=[],
        )
    return ConsistencyResponse(session_id=session_id, consistency=consistency)
