"""Unit tests for setup history and pit exit detection.

Tests for _on_pit_exit logic (US2) and setup_history queryability (US3).
Module-level state is set directly before each test for isolation.
"""
import pytest

import ac_race_engineer as app
from buffer import SampleBuffer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_history_entry(contents, trigger="session_start", lap=0):
    return {
        "timestamp": "2026-03-03T10:00:00",
        "trigger": trigger,
        "lap": lap,
        "filename": "setup.ini" if contents is not None else None,
        "contents": contents,
        "confidence": "high" if contents is not None else None,
    }


def _setup_recording_state(tmp_path, monkeypatch, setup_return):
    """Prepare module state so _start_recording can run successfully."""
    app._config = {
        "output_dir": str(tmp_path),
        "buffer_size": 100,
        "flush_interval_s": 30.0,
        "log_level": "info",
        "sample_rate_hz": 25,
    }
    app._sim_info = None
    app._buffer = SampleBuffer(100)
    app._error_flag = False
    monkeypatch.setattr(app, "find_active_setup", lambda car, track: setup_return)


# ---------------------------------------------------------------------------
# US2 — Initial history entry (created by _start_recording)
# ---------------------------------------------------------------------------

class TestHistoryInitialEntry:

    def test_history_initial_entry(self, tmp_path, monkeypatch):
        """One entry is created at session start when a valid setup is found."""
        _setup_recording_state(tmp_path, monkeypatch, ("setup.ini", "[SETUP]\ntest=1\n", "high"))
        app._start_recording("car", "track")
        assert not app._error_flag
        history = app._session_metadata["setup_history"]
        assert len(history) == 1
        entry = history[0]
        assert entry["trigger"] == "session_start"
        assert entry["lap"] == 0
        assert entry["filename"] == "setup.ini"
        assert "[SETUP]" in entry["contents"]
        assert entry["confidence"] == "high"

    def test_history_initial_null_setup(self, tmp_path, monkeypatch):
        """One entry is created even when no setup file is found — all null."""
        _setup_recording_state(tmp_path, monkeypatch, (None, None, None))
        app._start_recording("car", "track")
        assert not app._error_flag
        history = app._session_metadata["setup_history"]
        assert len(history) == 1
        entry = history[0]
        assert entry["trigger"] == "session_start"
        assert entry["lap"] == 0
        assert entry["filename"] is None
        assert entry["contents"] is None
        assert entry["confidence"] is None


# ---------------------------------------------------------------------------
# US2 — Pit exit handling (_on_pit_exit)
# ---------------------------------------------------------------------------

class TestPitExitHandling:

    def _setup_pit_state(self, tmp_path, initial_contents):
        """Place module in STATE_RECORDING with one history entry."""
        meta_path = str(tmp_path / "test.meta.json")
        app._meta_filepath = meta_path
        app._session_metadata = {
            "setup_history": [_make_history_entry(initial_contents)]
        }
        return meta_path

    def test_pit_exit_with_change(self, tmp_path, monkeypatch):
        """Different contents → new entry appended and metadata rewritten."""
        self._setup_pit_state(tmp_path, "[SETUP]\nold=1\n")
        new_contents = "[SETUP]\nnew=2\n"
        written = []
        monkeypatch.setattr(app, "find_active_setup",
                            lambda car, track: ("setup2.ini", new_contents, "high"))
        monkeypatch.setattr(app, "write_early_metadata",
                            lambda path, meta: written.append((path, meta)))

        app._on_pit_exit("car", "track")

        history = app._session_metadata["setup_history"]
        assert len(history) == 2
        assert history[1]["trigger"] == "pit_exit"
        assert history[1]["contents"] == new_contents
        assert history[1]["filename"] == "setup2.ini"
        assert len(written) == 1

    def test_pit_exit_no_change(self, tmp_path, monkeypatch):
        """Identical contents → no new entry, metadata not rewritten."""
        same_contents = "[SETUP]\nsame=1\n"
        self._setup_pit_state(tmp_path, same_contents)
        written = []
        monkeypatch.setattr(app, "find_active_setup",
                            lambda car, track: ("setup.ini", same_contents, "high"))
        monkeypatch.setattr(app, "write_early_metadata",
                            lambda path, meta: written.append((path, meta)))

        app._on_pit_exit("car", "track")

        assert len(app._session_metadata["setup_history"]) == 1
        assert len(written) == 0

    def test_pit_exit_null_dedup(self, tmp_path, monkeypatch):
        """FR-011 over FR-012: null == null → no new entry appended."""
        self._setup_pit_state(tmp_path, None)
        written = []
        monkeypatch.setattr(app, "find_active_setup",
                            lambda car, track: (None, None, None))
        monkeypatch.setattr(app, "write_early_metadata",
                            lambda path, meta: written.append((path, meta)))

        app._on_pit_exit("car", "track")

        assert len(app._session_metadata["setup_history"]) == 1
        assert len(written) == 0

    def test_pit_exit_unreadable_file(self, tmp_path, monkeypatch):
        """find_active_setup returns (None, None, None) with prior real contents → null entry IS appended."""
        self._setup_pit_state(tmp_path, "[SETUP]\nold=1\n")
        written = []
        monkeypatch.setattr(app, "find_active_setup",
                            lambda car, track: (None, None, None))
        monkeypatch.setattr(app, "write_early_metadata",
                            lambda path, meta: written.append((path, meta)))

        app._on_pit_exit("car", "track")

        history = app._session_metadata["setup_history"]
        assert len(history) == 2
        assert history[1]["trigger"] == "pit_exit"
        assert history[1]["filename"] is None
        assert history[1]["contents"] is None
        assert history[1]["confidence"] is None
        assert len(written) == 1


# ---------------------------------------------------------------------------
# US3 — History is queryable by lap (T010)
# ---------------------------------------------------------------------------

class TestHistoryQueryableByLap:

    def test_history_queryable_by_lap(self):
        """A three-entry history returns the correct active setup for any lap number."""
        history = [
            {
                "timestamp": "2026-03-03T10:00:00",
                "trigger": "session_start",
                "lap": 0,
                "filename": "setup_a.ini",
                "contents": "[A]",
                "confidence": "high",
            },
            {
                "timestamp": "2026-03-03T10:30:00",
                "trigger": "pit_exit",
                "lap": 8,
                "filename": "setup_b.ini",
                "contents": "[B]",
                "confidence": "high",
            },
            {
                "timestamp": "2026-03-03T11:00:00",
                "trigger": "pit_exit",
                "lap": 15,
                "filename": "setup_c.ini",
                "contents": "[C]",
                "confidence": "medium",
            },
        ]

        def lookup(N):
            return [e for e in history if e["lap"] <= N][-1]

        assert lookup(0)["contents"] == "[A]"
        assert lookup(7)["contents"] == "[A]"
        assert lookup(8)["contents"] == "[B]"
        assert lookup(10)["contents"] == "[B]"
        assert lookup(15)["contents"] == "[C]"
        assert lookup(20)["contents"] == "[C]"
