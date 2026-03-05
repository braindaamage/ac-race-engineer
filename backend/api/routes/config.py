"""Config endpoints — GET /config, PATCH /config, GET /config/validate."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from fastapi import APIRouter, HTTPException, Request

from ac_engineer.config.io import read_config, update_config
from ac_engineer.config.models import VALID_LLM_PROVIDERS, VALID_UI_THEMES

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


class ConfigUpdateRequest(BaseModel):
    """Partial update — only provided fields are changed."""

    model_config = ConfigDict(extra="forbid")

    ac_install_path: str | None = None
    setups_path: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    ui_theme: str | None = None


class ConfigValidationResponse(BaseModel):
    ac_path_valid: bool
    setups_path_valid: bool
    llm_provider_valid: bool
    is_valid: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config_to_response(config) -> ConfigResponse:
    """Convert ACConfig to ConfigResponse, coercing None to empty string."""
    return ConfigResponse(
        ac_install_path=str(config.ac_install_path) if config.ac_install_path else "",
        setups_path=str(config.setups_path) if config.setups_path else "",
        llm_provider=config.llm_provider,
        llm_model=config.llm_model if config.llm_model else "",
        ui_theme=config.ui_theme,
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

    ac_path_valid = config.is_ac_configured
    setups_path_valid = config.is_setups_configured
    llm_provider_valid = bool(config.llm_provider) and config.llm_provider in VALID_LLM_PROVIDERS

    return ConfigValidationResponse(
        ac_path_valid=ac_path_valid,
        setups_path_valid=setups_path_valid,
        llm_provider_valid=llm_provider_valid,
        is_valid=ac_path_valid and setups_path_valid and llm_provider_valid,
    )
