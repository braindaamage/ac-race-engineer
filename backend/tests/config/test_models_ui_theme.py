"""Tests for ui_theme field in ACConfig model."""

from __future__ import annotations

import json

import pytest

from ac_engineer.config.models import ACConfig
from ac_engineer.config.io import read_config, write_config


class TestUIThemeField:
    def test_default_value_is_dark(self):
        config = ACConfig()
        assert config.ui_theme == "dark"

    def test_valid_dark_theme(self):
        config = ACConfig(ui_theme="dark")
        assert config.ui_theme == "dark"

    def test_valid_light_theme(self):
        config = ACConfig(ui_theme="light")
        assert config.ui_theme == "light"

    def test_invalid_theme_raises_validation_error(self):
        with pytest.raises(ValueError, match="ui_theme must be one of"):
            ACConfig(ui_theme="neon")

    def test_serialization_includes_ui_theme(self):
        config = ACConfig(ui_theme="light")
        data = config.model_dump()
        assert data["ui_theme"] == "light"

    def test_serialization_includes_ui_theme_default(self):
        config = ACConfig()
        data = config.model_dump()
        assert data["ui_theme"] == "dark"


class TestUIThemeRoundTrip:
    def test_write_and_read_preserves_ui_theme(self, tmp_path):
        path = tmp_path / "config.json"
        config = ACConfig(ui_theme="light")
        write_config(path, config)
        loaded = read_config(path)
        assert loaded.ui_theme == "light"

    def test_read_config_without_ui_theme_returns_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            json.dumps({"llm_provider": "anthropic"}),
            encoding="utf-8",
        )
        loaded = read_config(path)
        assert loaded.ui_theme == "dark"
