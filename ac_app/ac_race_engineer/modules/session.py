"""Session lifecycle state machine for AC Race Engineer.

Manages transitions between IDLE, RECORDING, and FINALIZING states.
Supports two detection modes:
  - Normal: uses sim_info shared memory (graphics.status)
  - Fallback: uses speed/position heuristics when sim_info is unavailable

Python 3.3 compatible.
"""

import time

# Session states
STATE_IDLE = 0
STATE_RECORDING = 1
STATE_FINALIZING = 2

# AC session status values (from sim_info.graphics.status)
AC_STATUS_OFF = 0
AC_STATUS_REPLAY = 1
AC_STATUS_LIVE = 2
AC_STATUS_PAUSE = 3

# Fallback detection constants
_FALLBACK_CONFIRM_COUNT = 3       # Consecutive positive detections to confirm start
_FALLBACK_STALL_TIMEOUT = 5.0     # Seconds of no movement to detect session end


class SessionManager(object):
    """Manages the recording session lifecycle.

    State machine:
        IDLE -> RECORDING: when AC status is LIVE (or fallback heuristic)
        RECORDING -> FINALIZING: when status leaves LIVE or car/track changes
        FINALIZING -> IDLE: after finalize() is called
    """

    def __init__(self, fallback_mode=False):
        self.state = STATE_IDLE
        self.current_car = None
        self.current_track = None
        self.fallback_mode = fallback_mode

        # Fallback detection state
        self._fb_confirm_count = 0
        self._fb_last_position = None
        self._fb_stall_start = None

    def check_session_start(self, car_name, track_name, session_status,
                            speed_kmh=None, normalized_position=None):
        """Check if a new session should start.

        In normal mode: transitions IDLE -> RECORDING if status is LIVE.
        In fallback mode: transitions IDLE -> RECORDING if car/track are
        non-empty AND (speed > 0.5 OR position > 0.01) for 3 consecutive
        detections.

        Returns:
            True if state changed to RECORDING, False otherwise
        """
        if self.state != STATE_IDLE:
            return False

        if not self.fallback_mode:
            # Normal mode: shared memory status
            if session_status == AC_STATUS_LIVE:
                self.state = STATE_RECORDING
                self.current_car = car_name
                self.current_track = track_name
                return True
            return False

        # Fallback mode: heuristic detection
        if not car_name or not track_name:
            self._fb_confirm_count = 0
            return False

        moving = False
        if speed_kmh is not None and speed_kmh > 0.5:
            moving = True
        if normalized_position is not None and normalized_position > 0.01:
            moving = True

        if moving:
            self._fb_confirm_count += 1
        else:
            self._fb_confirm_count = 0

        if self._fb_confirm_count >= _FALLBACK_CONFIRM_COUNT:
            self.state = STATE_RECORDING
            self.current_car = car_name
            self.current_track = track_name
            self._fb_confirm_count = 0
            self._fb_last_position = normalized_position
            self._fb_stall_start = None
            return True

        return False

    def check_session_end(self, car_name, track_name, session_status,
                          speed_kmh=None, normalized_position=None):
        """Check if the current session should end.

        In normal mode: transitions RECORDING -> FINALIZING if status
        leaves LIVE or car/track changes.
        In fallback mode: transitions RECORDING -> FINALIZING if car/track
        changes or vehicle is stalled for 5+ seconds.

        Returns:
            True if state changed to FINALIZING, False otherwise
        """
        if self.state != STATE_RECORDING:
            return False

        # Car or track change ends session in both modes
        if car_name != self.current_car or track_name != self.current_track:
            self.state = STATE_FINALIZING
            return True

        if not self.fallback_mode:
            # Normal mode: shared memory status
            if session_status != AC_STATUS_LIVE:
                self.state = STATE_FINALIZING
                return True
            return False

        # Fallback mode: stall detection
        is_stalled = (
            speed_kmh is not None
            and speed_kmh == 0
            and normalized_position is not None
            and self._fb_last_position is not None
            and normalized_position == self._fb_last_position
        )

        if is_stalled:
            now = time.time()
            if self._fb_stall_start is None:
                self._fb_stall_start = now
            elif now - self._fb_stall_start >= _FALLBACK_STALL_TIMEOUT:
                self.state = STATE_FINALIZING
                return True
        else:
            self._fb_stall_start = None

        # Update last known position
        if normalized_position is not None:
            self._fb_last_position = normalized_position

        return False

    def finalize(self):
        """Complete the finalization process and return to IDLE.

        Returns:
            True if state changed to IDLE, False otherwise
        """
        if self.state != STATE_FINALIZING:
            return False

        self.state = STATE_IDLE
        self.current_car = None
        self.current_track = None
        self._fb_confirm_count = 0
        self._fb_last_position = None
        self._fb_stall_start = None
        return True
