"""Car parameter resolution endpoints — GET /cars, DELETE /cars/cache, etc."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ac_engineer.config.io import read_config
from ac_engineer.resolver import (
    get_cached_parameters,
    invalidate_all_caches,
    invalidate_cache,
    list_cars,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class CarStatusResponse(BaseModel):
    car_name: str
    status: str
    tier: int | None = None
    has_defaults: bool | None = None
    resolved_at: str | None = None


class CarListResponse(BaseModel):
    cars: list[CarStatusResponse]
    total: int


class ParameterRangeResponse(BaseModel):
    section: str
    parameter: str
    min_value: float
    max_value: float
    step: float
    default_value: float | None = None


class CarParametersResponse(BaseModel):
    car_name: str
    tier: int
    has_defaults: bool
    resolved_at: str
    parameters: dict[str, ParameterRangeResponse]


class CacheInvalidateResponse(BaseModel):
    car_name: str
    invalidated: bool


class CacheInvalidateAllResponse(BaseModel):
    invalidated_count: int


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------


def _error_response(status: int, error_type: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "type": error_type,
                "message": message,
                "detail": None,
            }
        },
    )


# ---------------------------------------------------------------------------
# Routes — DELETE /cars/cache MUST be registered before /{car_name}/cache
# ---------------------------------------------------------------------------


@router.get("")
def get_cars(request: Request) -> CarListResponse:
    """List all installed cars with resolution status."""
    config = read_config(request.app.state.config_path)
    try:
        statuses = list_cars(config.ac_install_path, request.app.state.db_path)
    except ValueError as exc:
        return _error_response(  # type: ignore[return-value]
            400,
            "ac_path_not_configured",
            str(exc),
        )

    cars = [
        CarStatusResponse(
            car_name=s.car_name,
            status=s.status,
            tier=s.tier,
            has_defaults=s.has_defaults,
            resolved_at=s.resolved_at,
        )
        for s in statuses
    ]
    return CarListResponse(cars=cars, total=len(cars))


@router.delete("/cache")
def delete_all_caches(request: Request) -> CacheInvalidateAllResponse:
    """Invalidate all cached parameter data."""
    count = invalidate_all_caches(request.app.state.db_path)
    return CacheInvalidateAllResponse(invalidated_count=count)


@router.get("/{car_name}/parameters")
def get_car_parameters(car_name: str, request: Request):
    """Get cached parameter data for a specific car."""
    cached = get_cached_parameters(request.app.state.db_path, car_name)
    if cached is None:
        return _error_response(
            404,
            "not_cached",
            f"No cached parameter data for car '{car_name}'. "
            "Run an analysis session to trigger resolution.",
        )
    params = {
        key: ParameterRangeResponse(
            section=rng.section,
            parameter=rng.parameter,
            min_value=rng.min_value,
            max_value=rng.max_value,
            step=rng.step,
            default_value=rng.default_value,
        )
        for key, rng in cached.parameters.items()
    }
    return CarParametersResponse(
        car_name=cached.car_name,
        tier=int(cached.tier),
        has_defaults=cached.has_defaults,
        resolved_at=cached.resolved_at,
        parameters=params,
    )


@router.delete("/{car_name}/cache")
def delete_car_cache(car_name: str, request: Request):
    """Invalidate cached parameter data for a specific car."""
    deleted = invalidate_cache(request.app.state.db_path, car_name)
    if not deleted:
        return _error_response(
            404,
            "not_cached",
            f"No cached data found for car '{car_name}'.",
        )
    return CacheInvalidateResponse(car_name=car_name, invalidated=True)
