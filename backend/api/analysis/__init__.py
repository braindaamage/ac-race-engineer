"""Analysis package — orchestration, caching, and serialization for analysis endpoints."""

from api.analysis.cache import get_cache_dir, load_analyzed_session, save_analyzed_session
from api.analysis.models import (
    AggregatedCorner,
    ConsistencyResponse,
    CornerDetailResponse,
    CornerLapEntry,
    CornerListResponse,
    LapDetailResponse,
    LapListResponse,
    LapSummary,
    ProcessResponse,
    StintComparisonResponse,
    StintListResponse,
)
from api.analysis.pipeline import make_processing_job
from api.analysis.serializers import aggregate_corners, get_corner_by_lap, summarize_all_laps, summarize_lap

__all__ = [
    "get_cache_dir",
    "load_analyzed_session",
    "save_analyzed_session",
    "make_processing_job",
    "summarize_lap",
    "summarize_all_laps",
    "aggregate_corners",
    "get_corner_by_lap",
    "AggregatedCorner",
    "ConsistencyResponse",
    "CornerDetailResponse",
    "CornerLapEntry",
    "CornerListResponse",
    "LapDetailResponse",
    "LapListResponse",
    "LapSummary",
    "ProcessResponse",
    "StintComparisonResponse",
    "StintListResponse",
]
