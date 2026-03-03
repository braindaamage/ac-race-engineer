"""Unit tests for status indicator module."""
from status import (
    STATUS_IDLE, STATUS_RECORDING, STATUS_FLUSHING, STATUS_ERROR,
    get_status_display,
)


class TestStatusDisplay:
    def test_idle_state(self):
        text, r, g, b = get_status_display(STATUS_IDLE)
        assert text == "IDLE"
        assert 0.0 <= r <= 1.0
        assert 0.0 <= g <= 1.0
        assert 0.0 <= b <= 1.0

    def test_recording_state(self):
        text, r, g, b = get_status_display(STATUS_RECORDING)
        assert text == "REC"
        assert g > r  # green dominant
        assert g > b

    def test_flushing_state(self):
        text, r, g, b = get_status_display(STATUS_FLUSHING)
        assert text == "FLUSH"
        assert r > 0  # yellow (r + g)
        assert g > 0

    def test_error_state(self):
        text, r, g, b = get_status_display(STATUS_ERROR)
        assert text == "ERR"
        assert r > g  # red dominant
        assert r > b

    def test_all_four_states_covered(self):
        states = [STATUS_IDLE, STATUS_RECORDING, STATUS_FLUSHING, STATUS_ERROR]
        texts = set()
        for state in states:
            text, r, g, b = get_status_display(state)
            texts.add(text)
            assert isinstance(r, float)
            assert isinstance(g, float)
            assert isinstance(b, float)
        assert len(texts) == 4  # all unique
