"""Sample buffer for AC Race Engineer.

In-memory buffer for accumulating telemetry samples before disk flush.
Python 3.3 compatible.
"""
import time


class SampleBuffer(object):
    """Buffer that accumulates telemetry sample rows before flushing to disk."""

    def __init__(self, max_size=1000):
        self._samples = []
        self._max_size = max_size
        self._last_flush_time = time.time()

    @property
    def count(self):
        """Number of buffered samples."""
        return len(self._samples)

    @property
    def max_size(self):
        return self._max_size

    def append(self, sample_row):
        """Add a sample row to the buffer.

        Returns True if the buffer is now full and needs flushing.
        """
        if len(self._samples) >= self._max_size:
            return True
        self._samples.append(sample_row)
        return len(self._samples) >= self._max_size

    def get_all(self):
        """Return all buffered rows and clear the buffer."""
        rows = list(self._samples)
        self._samples = []
        return rows

    def clear(self):
        """Clear the buffer."""
        self._samples = []

    def is_flush_due(self, flush_interval_s):
        """Check if enough time has elapsed since last flush."""
        return (time.time() - self._last_flush_time) >= flush_interval_s

    def mark_flushed(self):
        """Update the last flush timestamp."""
        self._last_flush_time = time.time()
