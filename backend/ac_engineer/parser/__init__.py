"""Public API for ac_engineer.parser."""

from ac_engineer.parser.models import (
    ParsedSession,
    SessionMetadata,
    LapSegment,
    CornerSegment,
    SetupEntry,
    SetupParameter,
    QualityWarning,
    LapClassification,
    WarnType,
    ParserError,
)

__all__ = [
    "parse_session",
    "save_session",
    "load_session",
    "ParsedSession",
    "SessionMetadata",
    "LapSegment",
    "CornerSegment",
    "SetupEntry",
    "SetupParameter",
    "QualityWarning",
    "LapClassification",
    "WarnType",
    "ParserError",
]


def parse_session(csv_path, meta_path) -> ParsedSession:
    """Parse a raw telemetry session into structured lap and corner segments."""
    from ac_engineer.parser.session_parser import parse_session as _parse
    return _parse(csv_path, meta_path)


def save_session(session: ParsedSession, output_dir, base_name=None):
    """Serialize a ParsedSession to Parquet + JSON format."""
    from ac_engineer.parser.cache import save_session as _save
    return _save(session, output_dir, base_name)


def load_session(session_dir) -> ParsedSession:
    """Load a ParsedSession from a previously saved intermediate format."""
    from ac_engineer.parser.cache import load_session as _load
    return _load(session_dir)
