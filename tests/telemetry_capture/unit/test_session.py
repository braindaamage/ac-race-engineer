"""Unit tests for session state machine."""
import time

from session import (
    SessionManager, STATE_IDLE, STATE_RECORDING, STATE_FINALIZING,
    AC_STATUS_LIVE, AC_STATUS_OFF, AC_STATUS_PAUSE,
    _FALLBACK_CONFIRM_COUNT, _FALLBACK_STALL_TIMEOUT,
)


class TestSessionManagerNormalMode:
    """Tests for normal mode (sim_info available)."""

    def test_idle_to_recording_on_live_status(self):
        mgr = SessionManager()
        assert mgr.state == STATE_IDLE
        changed = mgr.check_session_start("car", "track", AC_STATUS_LIVE)
        assert changed is True
        assert mgr.state == STATE_RECORDING

    def test_recording_to_finalizing_on_status_change(self):
        mgr = SessionManager()
        mgr.check_session_start("car", "track", AC_STATUS_LIVE)
        changed = mgr.check_session_end("car", "track", AC_STATUS_OFF)
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_recording_to_finalizing_on_car_change(self):
        mgr = SessionManager()
        mgr.check_session_start("car1", "track", AC_STATUS_LIVE)
        changed = mgr.check_session_end("car2", "track", AC_STATUS_LIVE)
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_recording_to_finalizing_on_track_change(self):
        mgr = SessionManager()
        mgr.check_session_start("car", "track1", AC_STATUS_LIVE)
        changed = mgr.check_session_end("car", "track2", AC_STATUS_LIVE)
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_finalizing_to_idle_after_finalize(self):
        mgr = SessionManager()
        mgr.check_session_start("car", "track", AC_STATUS_LIVE)
        mgr.check_session_end("car", "track", AC_STATUS_OFF)
        changed = mgr.finalize()
        assert changed is True
        assert mgr.state == STATE_IDLE

    def test_stays_idle_when_not_live(self):
        mgr = SessionManager()
        changed = mgr.check_session_start("car", "track", AC_STATUS_OFF)
        assert changed is False
        assert mgr.state == STATE_IDLE

    def test_stays_idle_when_paused(self):
        mgr = SessionManager()
        changed = mgr.check_session_start("car", "track", AC_STATUS_PAUSE)
        assert changed is False
        assert mgr.state == STATE_IDLE

    def test_recording_stays_recording_when_same_car_track(self):
        mgr = SessionManager()
        mgr.check_session_start("car", "track", AC_STATUS_LIVE)
        changed = mgr.check_session_end("car", "track", AC_STATUS_LIVE)
        assert changed is False
        assert mgr.state == STATE_RECORDING

    def test_finalize_from_idle_returns_false(self):
        mgr = SessionManager()
        assert mgr.finalize() is False

    def test_check_session_start_from_recording_returns_false(self):
        mgr = SessionManager()
        mgr.check_session_start("car", "track", AC_STATUS_LIVE)
        changed = mgr.check_session_start("car2", "track2", AC_STATUS_LIVE)
        assert changed is False

    def test_normal_mode_ignores_speed_kwargs(self):
        """Normal mode should not use speed/position kwargs."""
        mgr = SessionManager(fallback_mode=False)
        # Even with speed=0 and position=0, should start on LIVE status
        changed = mgr.check_session_start(
            "car", "track", AC_STATUS_LIVE,
            speed_kmh=0.0, normalized_position=0.0
        )
        assert changed is True


class TestSessionManagerFallbackMode:
    """Tests for fallback mode (sim_info unavailable)."""

    def test_fallback_mode_flag_defaults_to_false(self):
        mgr = SessionManager()
        assert mgr.fallback_mode is False

    def test_fallback_mode_flag_set_on_init(self):
        mgr = SessionManager(fallback_mode=True)
        assert mgr.fallback_mode is True

    def test_fallback_start_requires_confirmation_window(self):
        """Must have 3 consecutive positive detections to start."""
        mgr = SessionManager(fallback_mode=True)
        # First two detections: not enough
        for i in range(_FALLBACK_CONFIRM_COUNT - 1):
            changed = mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.1
            )
            assert changed is False
            assert mgr.state == STATE_IDLE

        # Third detection: confirmed
        changed = mgr.check_session_start(
            "car", "track", 0, speed_kmh=50.0, normalized_position=0.1
        )
        assert changed is True
        assert mgr.state == STATE_RECORDING

    def test_fallback_start_resets_count_on_no_movement(self):
        """Confirmation count resets if movement stops."""
        mgr = SessionManager(fallback_mode=True)
        # Two positive detections
        for _ in range(2):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.1
            )
        assert mgr._fb_confirm_count == 2

        # No movement: count resets
        mgr.check_session_start(
            "car", "track", 0, speed_kmh=0.0, normalized_position=0.0
        )
        assert mgr._fb_confirm_count == 0

    def test_fallback_start_resets_count_on_empty_car(self):
        """Confirmation count resets if car name is empty."""
        mgr = SessionManager(fallback_mode=True)
        mgr.check_session_start(
            "car", "track", 0, speed_kmh=50.0, normalized_position=0.1
        )
        assert mgr._fb_confirm_count == 1

        # Empty car name resets
        mgr.check_session_start(
            "", "track", 0, speed_kmh=50.0, normalized_position=0.1
        )
        assert mgr._fb_confirm_count == 0

    def test_fallback_start_detects_via_speed(self):
        """Speed > 0.5 alone is enough for positive detection."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=1.0, normalized_position=0.0
            )
        assert mgr.state == STATE_RECORDING

    def test_fallback_start_detects_via_position(self):
        """Position > 0.01 alone is enough for positive detection."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=0.0, normalized_position=0.05
            )
        assert mgr.state == STATE_RECORDING

    def test_fallback_end_on_car_change(self):
        """Session ends if car changes in fallback mode."""
        mgr = SessionManager(fallback_mode=True)
        # Start session
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car1", "track", 0, speed_kmh=50.0, normalized_position=0.1
            )
        assert mgr.state == STATE_RECORDING

        # Car changes
        changed = mgr.check_session_end(
            "car2", "track", 0, speed_kmh=50.0, normalized_position=0.2
        )
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_fallback_end_on_track_change(self):
        """Session ends if track changes in fallback mode."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track1", 0, speed_kmh=50.0, normalized_position=0.1
            )
        assert mgr.state == STATE_RECORDING

        changed = mgr.check_session_end(
            "car", "track2", 0, speed_kmh=50.0, normalized_position=0.2
        )
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_fallback_end_on_stall(self, monkeypatch):
        """Session ends after stall timeout (5+ seconds of no movement)."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.5
            )
        assert mgr.state == STATE_RECORDING

        # First check with speed=0, same position -> starts stall timer
        fake_time = [100.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])

        changed = mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert changed is False
        assert mgr._fb_stall_start == 100.0

        # After 4 seconds -> still not ended
        fake_time[0] = 104.0
        changed = mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert changed is False

        # After 5+ seconds -> session ends
        fake_time[0] = 105.1
        changed = mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert changed is True
        assert mgr.state == STATE_FINALIZING

    def test_fallback_stall_resets_on_movement(self, monkeypatch):
        """Stall timer resets if car starts moving again."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.5
            )

        fake_time = [100.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])

        # Start stalling
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert mgr._fb_stall_start == 100.0

        # Resume movement (speed > 0)
        fake_time[0] = 103.0
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=10.0, normalized_position=0.6
        )
        assert mgr._fb_stall_start is None

    def test_fallback_stall_resets_on_position_change(self, monkeypatch):
        """Stall timer resets if position changes (even with speed=0)."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.5
            )

        fake_time = [100.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])

        # Start stalling at position 0.5
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert mgr._fb_stall_start is not None

        # Position changed (still speed=0 but car rolled)
        fake_time[0] = 103.0
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.51
        )
        assert mgr._fb_stall_start is None

    def test_fallback_no_false_end_on_brief_stop(self, monkeypatch):
        """Brief stops (< 5s) should NOT end the session."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.5
            )

        fake_time = [100.0]
        monkeypatch.setattr(time, "time", lambda: fake_time[0])

        # Stop for 3 seconds
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        fake_time[0] = 103.0
        changed = mgr.check_session_end(
            "car", "track", 0, speed_kmh=0, normalized_position=0.5
        )
        assert changed is False

        # Resume movement
        fake_time[0] = 103.5
        mgr.check_session_end(
            "car", "track", 0, speed_kmh=30.0, normalized_position=0.6
        )
        assert mgr.state == STATE_RECORDING

    def test_fallback_finalize_resets_state(self):
        """Finalize clears all fallback tracking state."""
        mgr = SessionManager(fallback_mode=True)
        for _ in range(_FALLBACK_CONFIRM_COUNT):
            mgr.check_session_start(
                "car", "track", 0, speed_kmh=50.0, normalized_position=0.5
            )
        mgr.state = STATE_FINALIZING
        mgr.finalize()

        assert mgr.state == STATE_IDLE
        assert mgr._fb_confirm_count == 0
        assert mgr._fb_last_position is None
        assert mgr._fb_stall_start is None

    def test_fallback_ignores_session_status(self):
        """Fallback mode should not use session_status for start detection."""
        mgr = SessionManager(fallback_mode=True)
        # session_status=LIVE but no movement -> should NOT start
        changed = mgr.check_session_start(
            "car", "track", AC_STATUS_LIVE,
            speed_kmh=0.0, normalized_position=0.0
        )
        assert changed is False
