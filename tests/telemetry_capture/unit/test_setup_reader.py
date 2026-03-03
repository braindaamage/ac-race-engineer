"""Unit tests for setup_reader module."""
import os
import time
import pytest

from setup_reader import find_active_setup, _get_setups_base_dir


class TestFindActiveSetup:
    def _create_setup_dirs(self, tmp_path, car, track=None):
        """Helper to create setup directory structure."""
        if track:
            d = tmp_path / "setups" / car / track
        else:
            d = tmp_path / "setups" / car
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    def _write_setup(self, directory, name, content="[SETUP]\ntest=1\n", age_seconds=0):
        """Helper to create a setup file with controlled modification time."""
        filepath = os.path.join(directory, name)
        with open(filepath, "w") as f:
            f.write(content)
        if age_seconds > 0:
            mtime = time.time() - age_seconds
            os.utime(filepath, (mtime, mtime))
        return filepath

    def test_finds_ini_in_track_specific_dir(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "test_car", "test_track")
        self._write_setup(track_dir, "setup.ini")
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        filename, contents, confidence = find_active_setup("test_car", "test_track")
        assert filename == "setup.ini"
        assert "[SETUP]" in contents
        assert confidence == "high"

    def test_falls_back_to_generic_dir(self, tmp_path, monkeypatch):
        car_dir = self._create_setup_dirs(tmp_path, "test_car")
        self._write_setup(car_dir, "generic.ini")
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        filename, contents, confidence = find_active_setup("test_car", "nonexistent_track")
        assert filename == "generic.ini"
        assert confidence == "low"

    def test_returns_none_when_no_setups(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        filename, contents, confidence = find_active_setup("no_car", "no_track")
        assert filename is None
        assert contents is None
        assert confidence is None

    def test_confidence_high_single_recent(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "car", "track")
        self._write_setup(track_dir, "only.ini", age_seconds=10)
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        _, _, confidence = find_active_setup("car", "track")
        assert confidence == "high"

    def test_confidence_medium_multiple_files(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "car", "track")
        self._write_setup(track_dir, "setup1.ini", age_seconds=5)
        self._write_setup(track_dir, "setup2.ini", age_seconds=10)
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        _, _, confidence = find_active_setup("car", "track")
        assert confidence == "medium"

    def test_confidence_high_single_old_file(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "car", "track")
        self._write_setup(track_dir, "old.ini", age_seconds=700)
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        _, _, confidence = find_active_setup("car", "track")
        assert confidence == "high"

    def test_confidence_high_old_single(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "car", "track")
        self._write_setup(track_dir, "old.ini", age_seconds=48 * 3600)
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        _, _, confidence = find_active_setup("car", "track")
        assert confidence == "high"

    def test_confidence_medium_old_multiple(self, tmp_path, monkeypatch):
        track_dir = self._create_setup_dirs(tmp_path, "car", "track")
        self._write_setup(track_dir, "old1.ini", age_seconds=48 * 3600)
        self._write_setup(track_dir, "old2.ini", age_seconds=48 * 3600 + 60)
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: str(tmp_path / "setups")
        )
        _, _, confidence = find_active_setup("car", "track")
        assert confidence == "medium"

    def test_handles_ioerror_gracefully(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "setup_reader._get_setups_base_dir",
            lambda: "/nonexistent/path/that/does/not/exist"
        )
        filename, contents, confidence = find_active_setup("car", "track")
        assert filename is None
