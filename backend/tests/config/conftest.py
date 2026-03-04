"""Config test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.config import ACConfig


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    """Return a temporary config.json path."""
    return tmp_path / "config.json"


@pytest.fixture()
def sample_config() -> ACConfig:
    """Return a populated ACConfig for testing."""
    return ACConfig(
        ac_install_path=Path("C:/Games/Assetto Corsa"),
        setups_path=Path("C:/Games/Assetto Corsa/setups"),
        llm_provider="anthropic",
        llm_model="claude-sonnet-4-5",
    )
