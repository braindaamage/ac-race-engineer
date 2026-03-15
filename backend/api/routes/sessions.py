"""Session discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ac_engineer.config.io import read_config
from ac_engineer.resolver.ac_assets import (
    car_badge_path,
    read_car_info,
    read_track_info,
    track_preview_path,
)
from ac_engineer.storage.models import SessionRecord, SyncResult
from ac_engineer.storage.sessions import (
    delete_session,
    get_session,
    list_car_stats,
    list_sessions,
    list_track_stats,
)


class SessionListResponse(BaseModel):
    """Wrapper for the session list endpoint."""

    sessions: list[SessionRecord]


class CarStatsResponse(BaseModel):
    car_name: str
    display_name: str
    brand: str
    car_class: str
    badge_url: str | None
    track_count: int
    session_count: int
    last_session_date: str


class CarStatsListResponse(BaseModel):
    cars: list[CarStatsResponse]


class TrackStatsResponse(BaseModel):
    track_name: str
    track_config: str
    display_name: str
    country: str
    length_m: float | None
    preview_url: str | None
    session_count: int
    best_lap_time: float | None
    last_session_date: str


class TrackStatsListResponse(BaseModel):
    car_name: str
    car_display_name: str
    car_brand: str
    car_class: str
    badge_url: str | None
    track_count: int
    session_count: int
    last_session_date: str
    tracks: list[TrackStatsResponse]


router = APIRouter(prefix="/sessions")


@router.get("", response_model=SessionListResponse)
async def list_all_sessions(
    request: Request,
    car: str | None = None,
    track: str | None = None,
    track_config: str | None = None,
) -> SessionListResponse:
    db_path = request.app.state.db_path
    sessions = list_sessions(
        db_path, car=car, track=track, track_config=track_config,
    )
    return SessionListResponse(sessions=sessions)


@router.get("/grouped/cars", response_model=CarStatsListResponse)
async def get_grouped_cars(request: Request) -> CarStatsListResponse:
    db_path = request.app.state.db_path
    config = read_config(request.app.state.config_path)
    ac_cars_path = config.ac_cars_path
    stats = list_car_stats(db_path)
    cars: list[CarStatsResponse] = []
    for row in stats:
        car_name = row["car"]
        info = read_car_info(ac_cars_path, car_name)
        badge = car_badge_path(ac_cars_path, car_name)
        cars.append(
            CarStatsResponse(
                car_name=car_name,
                display_name=info.display_name,
                brand=info.brand,
                car_class=info.car_class,
                badge_url=f"/cars/{car_name}/badge" if badge else None,
                track_count=row["track_count"],
                session_count=row["session_count"],
                last_session_date=row["last_session_date"],
            )
        )
    return CarStatsListResponse(cars=cars)


@router.get("/grouped/cars/{car_name}/tracks", response_model=TrackStatsListResponse)
async def get_grouped_car_tracks(request: Request, car_name: str) -> TrackStatsListResponse:
    db_path = request.app.state.db_path
    config = read_config(request.app.state.config_path)
    ac_cars_path = config.ac_cars_path
    ac_tracks_path = config.ac_tracks_path

    car_info = read_car_info(ac_cars_path, car_name)
    badge = car_badge_path(ac_cars_path, car_name)

    car_stats = list_car_stats(db_path)
    car_agg = next((s for s in car_stats if s["car"] == car_name), None)

    track_rows = list_track_stats(db_path, car_name)
    tracks: list[TrackStatsResponse] = []
    for row in track_rows:
        track_name = row["track"]
        track_config = row["track_config"]
        info = read_track_info(ac_tracks_path, track_name, track_config)
        preview = track_preview_path(ac_tracks_path, track_name, track_config)
        preview_url = None
        if preview:
            preview_url = f"/tracks/{track_name}/preview"
            if track_config:
                preview_url += f"?config={track_config}"
        tracks.append(
            TrackStatsResponse(
                track_name=track_name,
                track_config=track_config,
                display_name=info.display_name,
                country=info.country,
                length_m=info.length_m,
                preview_url=preview_url,
                session_count=row["session_count"],
                best_lap_time=row["best_lap_time"],
                last_session_date=row["last_session_date"],
            )
        )

    return TrackStatsListResponse(
        car_name=car_name,
        car_display_name=car_info.display_name,
        car_brand=car_info.brand,
        car_class=car_info.car_class,
        badge_url=f"/cars/{car_name}/badge" if badge else None,
        track_count=car_agg["track_count"] if car_agg else 0,
        session_count=car_agg["session_count"] if car_agg else 0,
        last_session_date=car_agg["last_session_date"] if car_agg else "",
        tracks=tracks,
    )


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
