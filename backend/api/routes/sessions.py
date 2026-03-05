"""Session discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ac_engineer.storage.models import SessionRecord, SyncResult
from ac_engineer.storage.sessions import (
    delete_session,
    get_session,
    list_sessions,
)


class SessionListResponse(BaseModel):
    """Wrapper for the session list endpoint."""

    sessions: list[SessionRecord]


router = APIRouter(prefix="/sessions")


@router.get("", response_model=SessionListResponse)
async def list_all_sessions(
    request: Request, car: str | None = None
) -> SessionListResponse:
    db_path = request.app.state.db_path
    sessions = list_sessions(db_path, car=car)
    return SessionListResponse(sessions=sessions)


@router.get("/{session_id}", response_model=SessionRecord)
async def get_session_detail(request: Request, session_id: str) -> SessionRecord:
    db_path = request.app.state.db_path
    session = get_session(db_path, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return session


@router.post("/sync", response_model=SyncResult)
async def sync_sessions(request: Request) -> SyncResult:
    from api.watcher.scanner import scan_sessions_dir

    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir
    return scan_sessions_dir(sessions_dir, db_path)


@router.delete("/{session_id}", status_code=204)
async def delete_session_endpoint(request: Request, session_id: str) -> Response:
    db_path = request.app.state.db_path
    deleted = delete_session(db_path, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return Response(status_code=204)
