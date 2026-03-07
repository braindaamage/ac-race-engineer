"""Config file I/O — read, write, update with atomic writes."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from .models import ACConfig

logger = logging.getLogger(__name__)

LLM_MODEL_DEFAULTS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-5",
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-flash",
}


def get_effective_model(config: ACConfig) -> str:
    """Return the effective model name, using provider default if not explicitly set."""
    if config.llm_model is not None:
        return config.llm_model
    return LLM_MODEL_DEFAULTS[config.llm_provider]


def read_config(path: str | Path) -> ACConfig:
    """Read configuration from a JSON file. Never raises — returns defaults on any error."""
    try:
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return ACConfig.model_validate(data)
    except Exception as exc:
        logger.warning("Failed to read config from %s: %s", path, exc)
        return ACConfig()


def write_config(path: str | Path, config: ACConfig) -> None:
    """Write configuration to file atomically (tmp + os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            json.dumps(config.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp_path, path)
    except BaseException:
        # Clean up tmp file on failure
        tmp_path.unlink(missing_ok=True)
        raise


def update_config(path: str | Path, **kwargs: Any) -> ACConfig:
    """Partial update: read, apply overrides, write back. Returns updated config."""
    valid_fields = set(ACConfig.model_fields.keys())
    unknown = set(kwargs.keys()) - valid_fields
    if unknown:
        raise ValueError(f"Unknown config fields: {unknown}")

    current = read_config(path)
    updated = current.model_copy(update=kwargs)
    write_config(path, updated)
    return updated
