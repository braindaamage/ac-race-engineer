"""Unit tests for config_reader module."""
import os
import tempfile
import pytest

from config_reader import read_config, DEFAULTS


class TestReadConfig:
    def test_defaults_when_no_file(self):
        config = read_config("/nonexistent/path/config.ini")
        assert config["sample_rate_hz"] == 25
        assert config["buffer_size"] == 1000
        assert config["flush_interval_s"] == 30.0
        assert config["log_level"] == "info"
        assert "ac-race-engineer" in config["output_dir"]

    def test_valid_config_parsing(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text(
            "[SETTINGS]\n"
            "output_dir = /custom/path\n"
            "sample_rate_hz = 20\n"
            "buffer_size = 500\n"
            "flush_interval_s = 60\n"
            "log_level = debug\n"
        )
        config = read_config(str(cfg))
        assert config["output_dir"] == "/custom/path"
        assert config["sample_rate_hz"] == 20
        assert config["buffer_size"] == 500
        assert config["flush_interval_s"] == 60.0
        assert config["log_level"] == "debug"

    def test_sample_rate_clamped_low(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nsample_rate_hz = 5\n")
        config = read_config(str(cfg))
        assert config["sample_rate_hz"] == 20

    def test_sample_rate_clamped_high(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nsample_rate_hz = 100\n")
        config = read_config(str(cfg))
        assert config["sample_rate_hz"] == 30

    def test_buffer_size_clamped_low(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nbuffer_size = 10\n")
        config = read_config(str(cfg))
        assert config["buffer_size"] == 100

    def test_buffer_size_clamped_high(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nbuffer_size = 99999\n")
        config = read_config(str(cfg))
        assert config["buffer_size"] == 5000

    def test_flush_interval_clamped(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nflush_interval_s = 1\n")
        config = read_config(str(cfg))
        assert config["flush_interval_s"] == 5.0

    def test_missing_keys_use_defaults(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nsample_rate_hz = 22\n")
        config = read_config(str(cfg))
        assert config["sample_rate_hz"] == 22
        assert config["buffer_size"] == DEFAULTS["buffer_size"]
        assert config["flush_interval_s"] == DEFAULTS["flush_interval_s"]
        assert config["log_level"] == DEFAULTS["log_level"]

    def test_malformed_values_use_defaults(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text(
            "[SETTINGS]\n"
            "sample_rate_hz = notanumber\n"
            "buffer_size = abc\n"
        )
        config = read_config(str(cfg))
        assert config["sample_rate_hz"] == DEFAULTS["sample_rate_hz"]
        assert config["buffer_size"] == DEFAULTS["buffer_size"]

    def test_tilde_expansion_in_output_dir(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\noutput_dir = ~/my_sessions\n")
        config = read_config(str(cfg))
        assert "~" not in config["output_dir"]
        assert config["output_dir"].endswith("my_sessions")

    def test_invalid_log_level_uses_default(self, tmp_path):
        cfg = tmp_path / "config.ini"
        cfg.write_text("[SETTINGS]\nlog_level = verbose\n")
        config = read_config(str(cfg))
        assert config["log_level"] == "info"
