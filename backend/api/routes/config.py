"""Config endpoints — GET /config, PATCH /config, GET /config/validate, POST /config/validate-path, POST /config/validate-api-key."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict

from fastapi import APIRouter, HTTPException, Request

from ac_engineer.config.io import read_config, update_config
from ac_engineer.config.models import VALID_LLM_PROVIDERS, VALID_UI_THEMES

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ConfigResponse(BaseModel):
    """All fields are strings, never null."""

    ac_install_path: str
    setups_path: str
    llm_provider: str
    llm_model: str
    ui_theme: str
    api_key: str
    onboarding_completed: bool
    diagnostic_mode: bool


class ConfigUpdateRequest(BaseModel):
    """Partial update — only provided fields are changed."""

    model_config = ConfigDict(extra="forbid")

    ac_install_path: str | None = None
    setups_path: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    ui_theme: str | None = None
    api_key: str | None = None
    onboarding_completed: bool | None = None
    diagnostic_mode: bool | None = None


class PathValidationResult(BaseModel):
    status: str
    message: str


class ConfigValidationResponse(BaseModel):
    ac_path: PathValidationResult
    setups_path: PathValidationResult
    llm_provider: PathValidationResult
    onboarding_completed: bool
    is_valid: bool


class ConnectionTestResult(BaseModel):
    valid: bool
    message: str


class ValidatePathRequest(BaseModel):
    path: str
    path_type: str


class ValidateApiKeyRequest(BaseModel):
    provider: str
    api_key: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask_api_key(key: str | None) -> str:
    """Mask API key: show first 4 + last 4 chars with **** in between."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _config_to_response(config) -> ConfigResponse:
    """Convert ACConfig to ConfigResponse, coercing None to empty string."""
    return ConfigResponse(
        ac_install_path=str(config.ac_install_path) if config.ac_install_path else "",
        setups_path=str(config.setups_path) if config.setups_path else "",
        llm_provider=config.llm_provider,
        llm_model=config.llm_model if config.llm_model else "",
        ui_theme=config.ui_theme,
        api_key=_mask_api_key(config.api_key),
        onboarding_completed=config.onboarding_completed,
        diagnostic_mode=config.diagnostic_mode,
    )


def _validate_ac_install_path(path_str: str) -> PathValidationResult:
    """Validate an AC install path with detailed messages."""
    if not path_str.strip():
        return PathValidationResult(
            status="empty",
            message="Please provide the path to your Assetto Corsa installation.",
        )
    p = Path(path_str)
    if not p.exists():
        return PathValidationResult(
            status="not_found",
            message="Folder not found at this location.",
        )
    content = p / "content"
    if not content.exists():
        return PathValidationResult(
            status="warning",
            message="This folder doesn't appear to contain Assetto Corsa. Expected to find a 'content' subfolder.",
        )
    cars = content / "cars"
    if not cars.exists():
        return PathValidationResult(
            status="warning",
            message="Found 'content' folder but 'content/cars' is missing. This may not be a complete AC installation.",
        )
    tracks = content / "tracks"
    if not tracks.exists():
        return PathValidationResult(
            status="warning",
            message="Found 'content' folder but 'content/cars' is missing. This may not be a complete AC installation.",
        )
    return PathValidationResult(
        status="valid",
        message="Valid Assetto Corsa installation found.",
    )


def _validate_setups_path(path_str: str) -> PathValidationResult:
    """Validate a setups folder path with detailed messages."""
    if not path_str.strip():
        return PathValidationResult(
            status="empty",
            message="Please provide the path to your setup files.",
        )
    p = Path(path_str)
    if not p.exists() or not p.is_dir():
        return PathValidationResult(
            status="not_found",
            message="Folder not found at this location.",
        )
    return PathValidationResult(
        status="valid",
        message="Setups folder found.",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ConfigResponse)
async def get_config(request: Request) -> ConfigResponse:
    config_path = request.app.state.config_path
    config = read_config(config_path)
    return _config_to_response(config)


@router.patch("", response_model=ConfigResponse)
async def patch_config(request: Request, body: ConfigUpdateRequest) -> ConfigResponse:
    config_path = request.app.state.config_path
    fields = body.model_dump(exclude_unset=True)
    if fields:
        # Validate llm_provider before persisting
        if "llm_provider" in fields and fields["llm_provider"] not in VALID_LLM_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=f"llm_provider must be one of {VALID_LLM_PROVIDERS}, got {fields['llm_provider']!r}",
            )
        # Validate ui_theme before persisting
        if "ui_theme" in fields and fields["ui_theme"] not in VALID_UI_THEMES:
            raise HTTPException(
                status_code=422,
                detail=f"ui_theme must be one of {VALID_UI_THEMES}, got {fields['ui_theme']!r}",
            )
        config = update_config(config_path, **fields)
    else:
        config = read_config(config_path)
    return _config_to_response(config)


@router.get("/validate", response_model=ConfigValidationResponse)
async def validate_config(request: Request) -> ConfigValidationResponse:
    config_path = request.app.state.config_path
    config = read_config(config_path)

    ac_path_str = str(config.ac_install_path) if config.ac_install_path else ""
    setups_path_str = str(config.setups_path) if config.setups_path else ""

    ac_result = _validate_ac_install_path(ac_path_str)
    setups_result = _validate_setups_path(setups_path_str)

    llm_valid = bool(config.llm_provider) and config.llm_provider in VALID_LLM_PROVIDERS
    llm_result = PathValidationResult(
        status="valid" if llm_valid else "warning",
        message=f"Provider '{config.llm_provider}' is supported." if llm_valid else f"Unknown provider '{config.llm_provider}'.",
    )

    is_valid = ac_result.status == "valid" and setups_result.status == "valid"

    return ConfigValidationResponse(
        ac_path=ac_result,
        setups_path=setups_result,
        llm_provider=llm_result,
        onboarding_completed=config.onboarding_completed,
        is_valid=is_valid,
    )


@router.post("/validate-path", response_model=PathValidationResult)
async def validate_path(body: ValidatePathRequest) -> PathValidationResult:
    if body.path_type == "ac_install":
        return _validate_ac_install_path(body.path)
    elif body.path_type == "setups":
        return _validate_setups_path(body.path)
    else:
        raise HTTPException(
            status_code=422,
            detail=f"path_type must be 'ac_install' or 'setups', got {body.path_type!r}",
        )


PROVIDER_URLS = {
    "anthropic": "https://api.anthropic.com/v1/models",
    "openai": "https://api.openai.com/v1/models",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
}

PROVIDER_LABELS = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "gemini": "Google Gemini",
}


@router.post("/validate-api-key", response_model=ConnectionTestResult)
async def validate_api_key(body: ValidateApiKeyRequest) -> ConnectionTestResult:
    provider = body.provider
    api_key = body.api_key

    if provider not in PROVIDER_URLS:
        return ConnectionTestResult(
            valid=False,
            message=f"Unknown provider '{provider}'. Must be anthropic, openai, or gemini.",
        )

    label = PROVIDER_LABELS[provider]
    url = PROVIDER_URLS[provider]
    headers: dict[str, str] = {}

    if provider == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
    elif provider == "openai":
        headers["Authorization"] = f"Bearer {api_key}"
    elif provider == "gemini":
        url = f"{url}?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 200:
            return ConnectionTestResult(
                valid=True,
                message=f"API key is valid. Connected to {label} successfully.",
            )
        elif resp.status_code in (401, 403):
            return ConnectionTestResult(
                valid=False,
                message="Invalid API key. Please check the key and try again.",
            )
        elif resp.status_code == 429:
            return ConnectionTestResult(
                valid=False,
                message=f"Rate limited by {label}. The key appears valid — try again in a moment.",
            )
        else:
            return ConnectionTestResult(
                valid=False,
                message=f"Unexpected error from {label} (HTTP {resp.status_code}). The key may still be valid.",
            )
    except httpx.TimeoutException:
        return ConnectionTestResult(
            valid=False,
            message=f"Could not reach {label}. Check your internet connection.",
        )
    except httpx.ConnectError:
        return ConnectionTestResult(
            valid=False,
            message=f"Could not reach {label}. Check your internet connection.",
        )
    except Exception as exc:
        logger.warning("API key validation error: %s", exc)
        return ConnectionTestResult(
            valid=False,
            message=f"Could not reach {label}. Check your internet connection.",
        )
