"""Unit tests for lap_segmenter: segment_laps and classify_lap."""

import numpy as np
import pandas as pd
import pytest

from ac_engineer.parser.lap_segmenter import classify_lap, segment_laps
from ac_engineer.parser.models import ParserError
from tests.parser.conftest import CHANNELS, make_session_df


# ---------------------------------------------------------------------------
# segment_laps
# ---------------------------------------------------------------------------

class TestSegmentLaps:
    def test_raises_on_missing_lap_count(self):
        df = pd.DataFrame({"speed_kmh": [100, 110]})
        with pytest.raises(ParserError, match="lap_count"):
            segment_laps(df)

    def test_empty_dataframe_returns_empty_list(self):
        df = pd.DataFrame(columns=CHANNELS)
        result = segment_laps(df)
        assert result == []

    def test_single_lap_returns_one_segment(self):
        df = make_session_df([{"lap_number": 0, "n_samples": 100}])
        segs = segment_laps(df)
        assert len(segs) == 1
        assert len(segs[0]) == 100

    def test_zero_to_one_lap_count(self):
        df = make_session_df([
            {"lap_number": 0, "n_samples": 50},
            {"lap_number": 1, "n_samples": 50},
        ])
        segs = segment_laps(df)
        assert len(segs) == 2

    def test_ten_laps(self):
        lap_configs = [{"lap_number": i, "n_samples": 100} for i in range(10)]
        df = make_session_df(lap_configs)
        segs = segment_laps(df)
        assert len(segs) == 10

    def test_no_samples_lost(self):
        lap_configs = [{"lap_number": i, "n_samples": 77} for i in range(5)]
        df = make_session_df(lap_configs)
        segs = segment_laps(df)
        total = sum(len(s) for s in segs)
        assert total == len(df)

    def test_single_row_dataframe(self):
        df = make_session_df([{"lap_number": 0, "n_samples": 1}])
        segs = segment_laps(df)
        assert len(segs) == 1
        assert len(segs[0]) == 1

    def test_lap_count_values_preserved(self):
        df = make_session_df([
            {"lap_number": 3, "n_samples": 20},
            {"lap_number": 4, "n_samples": 20},
        ])
        segs = segment_laps(df)
        assert segs[0]["lap_count"].iloc[0] == 3.0
        assert segs[1]["lap_count"].iloc[0] == 4.0

    def test_segments_reset_index(self):
        df = make_session_df([
            {"lap_number": 0, "n_samples": 50},
            {"lap_number": 1, "n_samples": 50},
        ])
        segs = segment_laps(df)
        for seg in segs:
            assert seg.index[0] == 0


# ---------------------------------------------------------------------------
# classify_lap
# ---------------------------------------------------------------------------

def _make_lap_df(
    n: int = 100,
    in_pit_lane_start: int = 0,
    in_pit_lane_end: int = 0,
    in_pit_lane_mid: bool = False,
    lap_invalid: bool = False,
) -> pd.DataFrame:
    """Build a minimal lap DataFrame for classification tests."""
    data = {
        "in_pit_lane": [0.0] * n,
        "lap_invalid": [1.0 if lap_invalid else 0.0] * n,
        "speed_kmh": [120.0] * n,
        "normalized_position": [i / n for i in range(n)],
    }
    if in_pit_lane_start:
        data["in_pit_lane"][0] = 1.0
    if in_pit_lane_end:
        data["in_pit_lane"][-1] = 1.0
    if in_pit_lane_mid:
        mid = n // 2
        for j in range(mid, min(mid + 5, n)):
            data["in_pit_lane"][j] = 1.0
    return pd.DataFrame(data)


class TestClassifyLap:
    def test_flying_lap(self):
        lap = _make_lap_df()
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "flying"
        assert is_invalid is False

    def test_outlap_first_sample_in_pit(self):
        lap = _make_lap_df(in_pit_lane_start=1)
        cls, is_invalid = classify_lap(lap, is_first=True, is_last=False)
        assert cls == "outlap"
        assert is_invalid is False

    def test_inlap_last_sample_in_pit(self):
        lap = _make_lap_df(in_pit_lane_end=1)
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "inlap"
        assert is_invalid is False

    def test_incomplete_is_last(self):
        lap = _make_lap_df()
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=True)
        assert cls == "incomplete"

    def test_invalid_lap_flag(self):
        lap = _make_lap_df(lap_invalid=True)
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "invalid"
        assert is_invalid is True

    def test_outlap_with_invalid_flag(self):
        """outlap + lap_invalid==1 → classification=outlap, is_invalid=True."""
        lap = _make_lap_df(in_pit_lane_start=1, lap_invalid=True)
        cls, is_invalid = classify_lap(lap, is_first=True, is_last=False)
        assert cls == "outlap"
        assert is_invalid is True

    def test_inlap_with_invalid_flag(self):
        lap = _make_lap_df(in_pit_lane_end=1, lap_invalid=True)
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "inlap"
        assert is_invalid is True

    def test_incomplete_with_invalid_flag(self):
        lap = _make_lap_df(lap_invalid=True)
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=True)
        assert cls == "incomplete"
        assert is_invalid is True

    def test_empty_lap_df(self):
        lap = pd.DataFrame(columns=["in_pit_lane", "lap_invalid", "speed_kmh"])
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "incomplete"
        assert is_invalid is False

    def test_missing_in_pit_lane_column_still_classifies(self):
        """Should not crash if in_pit_lane column is absent."""
        lap = pd.DataFrame({"lap_invalid": [0.0] * 50})
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "flying"

    def test_pure_invalid_classification(self):
        """lap_invalid set, not in pit, not last → invalid."""
        lap = _make_lap_df(lap_invalid=True)
        cls, is_invalid = classify_lap(lap, is_first=False, is_last=False)
        assert cls == "invalid"
        assert is_invalid is True
