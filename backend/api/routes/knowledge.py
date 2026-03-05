"""Knowledge endpoints — search + session knowledge fragments."""

from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query, Request

from ac_engineer.knowledge import get_knowledge_for_signals, search_knowledge
from ac_engineer.knowledge.signals import detect_signals
from ac_engineer.storage.sessions import get_session

from api.analysis.cache import get_cache_dir, load_analyzed_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class KnowledgeFragmentResponse(BaseModel):
    source_file: str
    section_title: str
    content: str
    tags: list[str]


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeFragmentResponse]
    total: int


class SessionKnowledgeResponse(BaseModel):
    session_id: str
    signals: list[str]
    fragments: list[KnowledgeFragmentResponse]


# ---------------------------------------------------------------------------
# GET /knowledge/search
# ---------------------------------------------------------------------------


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_endpoint(q: str = Query("")) -> KnowledgeSearchResponse:
    q_stripped = q.strip()
    if not q_stripped:
        return KnowledgeSearchResponse(query="", results=[], total=0)

    all_results = search_knowledge(q_stripped)
    capped = all_results[:10]

    return KnowledgeSearchResponse(
        query=q_stripped,
        results=[
            KnowledgeFragmentResponse(
                source_file=f.source_file,
                section_title=f.section_title,
                content=f.content,
                tags=f.tags,
            )
            for f in capped
        ],
        total=len(all_results),
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/knowledge
# ---------------------------------------------------------------------------


@router.get("/sessions/{session_id}/knowledge", response_model=SessionKnowledgeResponse)
async def session_knowledge(request: Request, session_id: str) -> SessionKnowledgeResponse:
    db_path = request.app.state.db_path
    sessions_dir = request.app.state.sessions_dir

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

    cache_dir = get_cache_dir(sessions_dir, session_id)
    try:
        analyzed = load_analyzed_session(cache_dir)
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=409,
            detail="Cached results are corrupted or missing \u2014 re-process the session",
        )

    signals = detect_signals(analyzed)
    fragments = get_knowledge_for_signals(analyzed)

    return SessionKnowledgeResponse(
        session_id=session_id,
        signals=signals,
        fragments=[
            KnowledgeFragmentResponse(
                source_file=f.source_file,
                section_title=f.section_title,
                content=f.content,
                tags=f.tags,
            )
            for f in fragments
        ],
    )
