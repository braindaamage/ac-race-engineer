"""Tests for centralized path resolution (dev + frozen modes)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from api.paths import get_config_path, get_data_dir, get_db_path, get_sessions_dir


class TestDevMode:
    """In dev mode, paths resolve relative to the repo root."""

    def test_get_data_dir_is_absolute(self):
        result = get_data_dir()
        assert result.is_absolute()

    def test_get_data_dir_ends_with_data(self):
        result = get_data_dir()
        assert result.name == "data"

    def test_get_data_dir_parent_is_repo_root(self):
        result = get_data_dir()
        # repo root should contain backend/
        repo_root = result.parent
        assert (repo_root / "backend").is_dir()

    def test_get_db_path(self):
        result = get_db_path()
        assert result.is_absolute()
        assert result.name == "ac_engineer.db"
        assert result.parent == get_data_dir()

    def test_get_config_path(self):
        result = get_config_path()
        assert result.is_absolute()
        assert result.name == "config.json"
        assert result.parent == get_data_dir()

    def test_get_sessions_dir(self):
        result = get_sessions_dir()
        assert result.is_absolute()
        assert result.name == "sessions"
        assert result.parent == get_data_dir()


class TestFrozenMode:
    """In frozen (PyInstaller) mode, paths resolve relative to the exe directory."""

    def test_get_data_dir_frozen(self, tmp_path):
        fake_exe = tmp_path / "dist" / "ac_engineer.exe"
        fake_exe.parent.mkdir(parents=True, exist_ok=True)
        fake_exe.touch()

        with patch("api.paths.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys.executable = str(fake_exe)
            result = get_data_dir()

        assert result.is_absolute()
        assert result == fake_exe.parent / "data"

    def test_get_db_path_frozen(self, tmp_path):
        fake_exe = tmp_path / "dist" / "app.exe"
        fake_exe.parent.mkdir(parents=True, exist_ok=True)
        fake_exe.touch()

        with patch("api.paths.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys.executable = str(fake_exe)
            result = get_db_path()

        assert result == fake_exe.parent / "data" / "ac_engineer.db"

    def test_get_config_path_frozen(self, tmp_path):
        fake_exe = tmp_path / "dist" / "app.exe"
        fake_exe.parent.mkdir(parents=True, exist_ok=True)
        fake_exe.touch()

        with patch("api.paths.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys.executable = str(fake_exe)
            result = get_config_path()

        assert result == fake_exe.parent / "data" / "config.json"

    def test_get_sessions_dir_frozen(self, tmp_path):
        fake_exe = tmp_path / "dist" / "app.exe"
        fake_exe.parent.mkdir(parents=True, exist_ok=True)
        fake_exe.touch()

        with patch("api.paths.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys.executable = str(fake_exe)
            result = get_sessions_dir()

        assert result == fake_exe.parent / "data" / "sessions"

    def test_all_frozen_paths_are_absolute(self, tmp_path):
        fake_exe = tmp_path / "app.exe"
        fake_exe.touch()

        with patch("api.paths.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys.executable = str(fake_exe)
            assert get_data_dir().is_absolute()
            assert get_db_path().is_absolute()
            assert get_config_path().is_absolute()
            assert get_sessions_dir().is_absolute()
