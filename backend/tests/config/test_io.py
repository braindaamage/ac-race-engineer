"""Tests for config I/O — read, write, update, atomic writes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ac_engineer.config import (
    ACConfig,
    LLM_MODEL_DEFAULTS,
    get_effective_model,
    read_config,
    update_config,
    write_config,
)


class TestWriteAndReadRoundTrip:
    def test_round_trip(self, config_path: Path, sample_config: ACConfig) -> None:
        write_config(config_path, sample_config)
        loaded = read_config(config_path)
        assert loaded.ac_install_path == sample_config.ac_install_path
        assert loaded.llm_provider == sample_config.llm_provider
        assert loaded.llm_model == sample_config.llm_model

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "config.json"
        write_config(nested, ACConfig())
        assert nested.exists()


class TestReadConfigFallbacks:
    def test_missing_file_returns_defaults(self, config_path: Path) -> None:
        config = read_config(config_path)
        assert config == ACConfig()

    def test_corrupt_json_returns_defaults(self, config_path: Path) -> None:
        config_path.write_text("{invalid json!!!", encoding="utf-8")
        config = read_config(config_path)
        assert config == ACConfig()

    def test_invalid_types_returns_defaults(self, config_path: Path) -> None:
        config_path.write_text(
            json.dumps({"llm_provider": 12345}), encoding="utf-8"
        )
        config = read_config(config_path)
        assert config == ACConfig()

    def test_unknown_fields_ignored(self, config_path: Path) -> None:
        config_path.write_text(
            json.dumps({"llm_provider": "openai", "unknown_field": "value"}),
            encoding="utf-8",
        )
        config = read_config(config_path)
        assert config.llm_provider == "openai"


class TestAtomicWrite:
    def test_no_tmp_file_left(self, config_path: Path) -> None:
        write_config(config_path, ACConfig())
        tmp_file = config_path.with_suffix(".tmp")
        assert not tmp_file.exists()


class TestUpdateConfig:
    def test_partial_update_preserves_fields(self, config_path: Path) -> None:
        write_config(config_path, ACConfig(llm_provider="openai", llm_model="gpt-4o"))
        updated = update_config(config_path, llm_model="gpt-4-turbo")
        assert updated.llm_provider == "openai"  # preserved
        assert updated.llm_model == "gpt-4-turbo"  # updated

    def test_unknown_field_raises(self, config_path: Path) -> None:
        write_config(config_path, ACConfig())
        with pytest.raises(ValueError, match="Unknown config fields"):
            update_config(config_path, nonexistent_field="value")

    def test_update_persists(self, config_path: Path) -> None:
        write_config(config_path, ACConfig())
        update_config(config_path, llm_provider="gemini")
        reloaded = read_config(config_path)
        assert reloaded.llm_provider == "gemini"


class TestGetEffectiveModel:
    def test_explicit_model(self) -> None:
        config = ACConfig(llm_model="my-custom-model")
        assert get_effective_model(config) == "my-custom-model"

    @pytest.mark.parametrize(
        "provider,expected",
        [
            ("anthropic", "claude-sonnet-4-5"),
            ("openai", "gpt-4o"),
            ("gemini", "gemini-3-flash-preview"),
        ],
    )
    def test_default_per_provider(self, provider: str, expected: str) -> None:
        config = ACConfig(llm_provider=provider)
        assert get_effective_model(config) == expected

    def test_defaults_dict_matches(self) -> None:
        assert set(LLM_MODEL_DEFAULTS.keys()) == {"anthropic", "openai", "gemini"}
