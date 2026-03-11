"""Tests for ACConfig Pydantic v2 model."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.config import ACConfig


class TestACConfigDefaults:
    def test_default_values(self) -> None:
        config = ACConfig()
        assert config.ac_install_path is None
        assert config.setups_path is None
        assert config.llm_provider == "anthropic"
        assert config.llm_model is None
        assert config.diagnostic_mode is False

    def test_with_explicit_values(self) -> None:
        config = ACConfig(
            ac_install_path=Path("C:/Games/AC"),
            setups_path=Path("C:/Setups"),
            llm_provider="openai",
            llm_model="gpt-4o",
        )
        assert config.ac_install_path == Path("C:/Games/AC")
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4o"


class TestLLMProviderValidator:
    @pytest.mark.parametrize("provider", ["anthropic", "openai", "gemini"])
    def test_valid_providers(self, provider: str) -> None:
        config = ACConfig(llm_provider=provider)
        assert config.llm_provider == provider

    def test_invalid_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_provider must be one of"):
            ACConfig(llm_provider="invalid")


class TestEmptyStringCoercion:
    def test_empty_ac_install_path_becomes_none(self) -> None:
        config = ACConfig(ac_install_path="")
        assert config.ac_install_path is None

    def test_empty_setups_path_becomes_none(self) -> None:
        config = ACConfig(setups_path="")
        assert config.setups_path is None

    def test_empty_llm_model_becomes_none(self) -> None:
        config = ACConfig(llm_model="")
        assert config.llm_model is None

    def test_whitespace_only_becomes_none(self) -> None:
        config = ACConfig(ac_install_path="   ")
        assert config.ac_install_path is None


class TestDiagnosticMode:
    def test_defaults_to_false(self) -> None:
        config = ACConfig()
        assert config.diagnostic_mode is False

    def test_serializes_diagnostic_mode(self) -> None:
        config = ACConfig(diagnostic_mode=True)
        data = config.model_dump()
        assert data["diagnostic_mode"] is True

    def test_round_trip(self) -> None:
        config = ACConfig(diagnostic_mode=True)
        data = config.model_dump()
        restored = ACConfig.model_validate(data)
        assert restored.diagnostic_mode is True


class TestPathSerialization:
    def test_round_trip(self) -> None:
        config = ACConfig(ac_install_path=Path("C:/Games/AC"))
        data = config.model_dump()
        assert data["ac_install_path"] == "C:\\Games\\AC"
        restored = ACConfig.model_validate(data)
        assert restored.ac_install_path == Path("C:/Games/AC")

    def test_none_paths_serialize_as_none(self) -> None:
        config = ACConfig()
        data = config.model_dump()
        assert data["ac_install_path"] is None
        assert data["setups_path"] is None


class TestComputedProperties:
    def test_ac_cars_path(self) -> None:
        config = ACConfig(ac_install_path=Path("C:/Games/AC"))
        assert config.ac_cars_path == Path("C:/Games/AC/content/cars")

    def test_ac_tracks_path(self) -> None:
        config = ACConfig(ac_install_path=Path("C:/Games/AC"))
        assert config.ac_tracks_path == Path("C:/Games/AC/content/tracks")

    def test_paths_none_when_no_install(self) -> None:
        config = ACConfig()
        assert config.ac_cars_path is None
        assert config.ac_tracks_path is None

    def test_is_ac_configured_with_real_dir(self, tmp_path: Path) -> None:
        config = ACConfig(ac_install_path=tmp_path)
        assert config.is_ac_configured is True

    def test_is_ac_configured_nonexistent(self) -> None:
        config = ACConfig(ac_install_path=Path("C:/nonexistent/path"))
        assert config.is_ac_configured is False

    def test_is_setups_configured_with_real_dir(self, tmp_path: Path) -> None:
        config = ACConfig(setups_path=tmp_path)
        assert config.is_setups_configured is True

    def test_is_setups_configured_nonexistent(self) -> None:
        config = ACConfig(setups_path=Path("C:/nonexistent/path"))
        assert config.is_setups_configured is False
