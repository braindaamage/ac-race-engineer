"""Global exception handlers for uniform error responses."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from api.errors.models import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

_STATUS_TO_TYPE: dict[int, str] = {
    404: "not_found",
    422: "validation_error",
}


def _error_json(status: int, error_type: str, message: str, detail: object = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(type=error_type, message=message, detail=detail))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


class CatchAllMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return a uniform 500 JSON response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled exception")
            return _error_json(500, "internal_error", "Internal server error")


def register_error_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the app."""

    # Middleware for catch-all 500 errors (works reliably across Starlette versions)
    app.add_middleware(CatchAllMiddleware)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_type = _STATUS_TO_TYPE.get(exc.status_code, f"http_{exc.status_code}")
        return _error_json(exc.status_code, error_type, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_json(422, "validation_error", "Validation error", exc.errors())
