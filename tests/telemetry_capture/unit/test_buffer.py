"""Unit tests for buffer module."""
import time
from buffer import SampleBuffer


class TestSampleBuffer:
    def test_append_increments_count(self):
        buf = SampleBuffer(max_size=100)
        buf.append([1, 2, 3])
        assert buf.count == 1
        buf.append([4, 5, 6])
        assert buf.count == 2

    def test_get_all_returns_all_rows_and_clears(self):
        buf = SampleBuffer(max_size=100)
        buf.append([1, 2, 3])
        buf.append([4, 5, 6])
        rows = buf.get_all()
        assert len(rows) == 2
        assert rows[0] == [1, 2, 3]
        assert rows[1] == [4, 5, 6]
        assert buf.count == 0

    def test_clear_resets_count(self):
        buf = SampleBuffer(max_size=100)
        buf.append([1, 2, 3])
        buf.append([4, 5, 6])
        buf.clear()
        assert buf.count == 0

    def test_empty_buffer_get_all_returns_empty(self):
        buf = SampleBuffer(max_size=100)
        rows = buf.get_all()
        assert rows == []

    def test_append_returns_true_when_full(self):
        buf = SampleBuffer(max_size=3)
        assert buf.append([1]) is False
        assert buf.append([2]) is False
        assert buf.append([3]) is True

    def test_is_flush_due_returns_false_before_interval(self):
        buf = SampleBuffer(max_size=100)
        buf.mark_flushed()
        assert buf.is_flush_due(30.0) is False

    def test_mark_flushed_resets_timer(self):
        buf = SampleBuffer(max_size=100)
        # Artificially set old flush time
        buf._last_flush_time = time.time() - 100
        assert buf.is_flush_due(30.0) is True
        buf.mark_flushed()
        assert buf.is_flush_due(30.0) is False

    def test_buffer_refuses_to_exceed_max_size(self):
        """T033/T035: Buffer enforces max_size bound."""
        buf = SampleBuffer(max_size=3)
        buf.append([1])
        buf.append([2])
        full = buf.append([3])
        assert full is True
        assert buf.count == 3
        # Attempting to append when full should signal full immediately
        still_full = buf.append([4])
        assert still_full is True
        # Buffer should not have grown past max_size
        assert buf.count == 3

    def test_is_flush_due_returns_true_after_interval(self):
        """T031: is_flush_due returns True after interval elapsed."""
        buf = SampleBuffer(max_size=100)
        buf._last_flush_time = time.time() - 35
        assert buf.is_flush_due(30.0) is True
