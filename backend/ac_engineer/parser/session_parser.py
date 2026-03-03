"""Main entry point for the telemetry parser pipeline.

Orchestrates all submodules to transform a raw CSV + .meta.json into a
fully structured ParsedSession Pydantic model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ac_engineer.parser.lap_segmenter import classify_lap, segment_laps
from ac_engineer.parser.models import (
    LapSegment,
    ParsedSession,
    ParserError,
    SessionMetadata,
    SetupEntry,
)
from ac_engineer.parser.setup_parser import associate_setup, parse_ini
from ac_engineer.parser.corner_detector import (
    build_reference_map,
    compute_session_thresholds,
    detect_corners,
)
from ac_engineer.parser.quality_validator import validate_lap


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_metadata(meta_path: Path, csv_path: Path | None = None) -> dict:
    """Read and normalise .meta.json; handle v1.0 legacy and crash recovery.

    Detects v1.0 metadata (missing ``setup_history`` key) and converts the
    flat ``setup_filename``/``setup_contents``/``setup_confidence`` fields to
    a single-entry ``setup_history`` array.

    Args:
        meta_path: Path to the .meta.json sidecar.
        csv_path: Optional CSV path used for crash recovery field derivation.

    Returns:
        Normalised metadata dict in v2.0 format.

    Raises:
        FileNotFoundError: If meta_path does not exist.
        ValueError: If the JSON is unparseable.
    """
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed metadata JSON: {meta_path}") from exc

    # v1.0 → v2.0 upgrade: wrap flat setup fields into setup_history
    if "setup_history" not in meta:
        meta["setup_history"] = [
            {
                "timestamp": meta.get("session_start", ""),
                "trigger": "session_start",
                "lap": 0,
                "filename": meta.get("setup_filename"),
                "contents": meta.get("setup_contents"),
                "confidence": meta.get("setup_confidence"),
            }
        ]

    return meta


def _read_csv(csv_path: Path) -> pd.DataFrame:
    """Read the session CSV and validate required columns.

    Args:
        csv_path: Path to the session CSV file.

    Returns:
        DataFrame with all 82 channel columns.

    Raises:
        FileNotFoundError: If csv_path does not exist.
        ParserError: If ``lap_count`` or ``normalized_position`` columns are missing.
        ValueError: If the CSV is empty.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError(f"CSV file is empty: {csv_path}")

    for required in ("lap_count", "normalized_position"):
        if required not in df.columns:
            raise ParserError(f"Required column '{required}' missing from CSV: {csv_path}")

    return df


def _derive_crash_fields(meta: dict, df: pd.DataFrame) -> dict:
    """Derive null crash-recovery fields from the CSV data.

    When the game crashes, ``session_end``, ``total_samples``, and
    ``sample_rate_hz`` are ``None`` in the metadata. This function derives
    them from the CSV.

    Args:
        meta: Metadata dict (mutated in place).
        df: Full session DataFrame.

    Returns:
        Updated metadata dict.
    """
    if meta.get("total_samples") is None:
        meta["total_samples"] = len(df)

    if meta.get("session_end") is None and "timestamp" in df.columns:
        last_ts = df["timestamp"].iloc[-1]
        # Convert Unix epoch to ISO 8601
        import datetime
        meta["session_end"] = datetime.datetime.utcfromtimestamp(last_ts).isoformat()

    if meta.get("sample_rate_hz") is None and "timestamp" in df.columns and len(df) > 1:
        intervals = df["timestamp"].diff().dropna()
        median_interval = intervals.median()
        if median_interval > 0:
            meta["sample_rate_hz"] = round(1.0 / median_interval, 2)

    return meta


def _build_session_metadata(meta: dict, df: pd.DataFrame) -> SessionMetadata:
    """Build SessionMetadata model from the normalised metadata dict.

    Args:
        meta: Normalised metadata dict.
        df: Full session DataFrame (used to compute channels_available/unavailable).

    Returns:
        Populated SessionMetadata model.
    """
    # Detect available channels from the CSV (non-all-NaN columns)
    channels_available = [c for c in df.columns if not df[c].isna().all()]
    channels_unavailable = [c for c in df.columns if df[c].isna().all()]

    # If metadata already has channel lists, prefer those; fall back to computed
    ch_avail = meta.get("channels_available") or channels_available
    ch_unavail = meta.get("channels_unavailable") or channels_unavailable

    return SessionMetadata(
        car_name=meta.get("car_name", ""),
        track_name=meta.get("track_name", ""),
        track_config=meta.get("track_config", ""),
        track_length_m=meta.get("track_length_m"),
        session_type=meta.get("session_type", ""),
        tyre_compound=meta.get("tyre_compound", ""),
        driver_name=meta.get("driver_name", ""),
        air_temp_c=meta.get("air_temp_c"),
        road_temp_c=meta.get("road_temp_c"),
        session_start=meta.get("session_start", ""),
        session_end=meta.get("session_end"),
        laps_completed=meta.get("laps_completed"),
        total_samples=meta.get("total_samples"),
        sample_rate_hz=meta.get("sample_rate_hz"),
        channels_available=ch_avail,
        channels_unavailable=ch_unavail,
        sim_info_available=meta.get("sim_info_available", True),
        reduced_mode=meta.get("reduced_mode", False),
        csv_filename=meta.get("csv_filename", ""),
        app_version=meta.get("app_version", ""),
    )


def _build_setup_entries(meta: dict) -> list[SetupEntry]:
    """Build SetupEntry models from the setup_history in metadata.

    Args:
        meta: Normalised metadata dict (v2.0 format with setup_history key).

    Returns:
        List of SetupEntry objects ordered by lap_start.
    """
    entries: list[SetupEntry] = []
    for entry_dict in meta.get("setup_history", []):
        contents = entry_dict.get("contents")
        parameters = parse_ini(contents)
        entries.append(SetupEntry(
            lap_start=int(entry_dict.get("lap", 0)),
            trigger=entry_dict.get("trigger", "session_start"),
            confidence=entry_dict.get("confidence"),
            filename=entry_dict.get("filename"),
            timestamp=entry_dict.get("timestamp", ""),
            parameters=parameters,
        ))
    return sorted(entries, key=lambda e: e.lap_start)


def _df_to_data_dict(lap_df: pd.DataFrame) -> dict[str, list]:
    """Convert a lap DataFrame to a dict[str, list] with NaN replaced by None.

    Args:
        lap_df: DataFrame for one lap.

    Returns:
        Dict mapping channel name → list of values (NaN → None).
    """
    result: dict[str, list] = {}
    for col in lap_df.columns:
        values = lap_df[col].tolist()
        result[col] = [None if (isinstance(v, float) and (v != v)) else v for v in values]
    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_session(csv_path: Path, meta_path: Path) -> ParsedSession:
    """Parse a raw telemetry session into structured lap and corner segments.

    Reads the CSV telemetry file and its .meta.json sidecar, segments the
    continuous data stream into individual laps, classifies each lap, and
    assembles a fully structured ParsedSession model.

    Args:
        csv_path: Absolute path to the session CSV file.
        meta_path: Absolute path to the session .meta.json sidecar.

    Returns:
        ParsedSession with all laps, metadata, and placeholder corners/setups.

    Raises:
        FileNotFoundError: If csv_path or meta_path does not exist.
        ValueError: If the CSV is empty or metadata JSON is unparseable.
        ParserError: If lap_count column is missing from the CSV.
    """
    csv_path = Path(csv_path)
    meta_path = Path(meta_path)

    # Step 1: Read and normalise metadata
    meta = _read_metadata(meta_path, csv_path)

    # Step 2: Read CSV
    df = _read_csv(csv_path)

    # Step 2b: Crash recovery — derive null fields from CSV
    meta = _derive_crash_fields(meta, df)

    # Step 3: Segment laps
    lap_dfs = segment_laps(df)

    # Step 4: Classify each lap
    n_laps = len(lap_dfs)
    classified: list[tuple[pd.DataFrame, str, bool, bool]] = []  # (df, cls, is_invalid, is_last)
    for i, lap_df in enumerate(lap_dfs):
        is_first = i == 0
        is_last = i == n_laps - 1
        classification, is_invalid = classify_lap(lap_df, is_first=is_first, is_last=is_last)
        classified.append((lap_df, classification, is_invalid, is_last))

    # Step 5: Quality validation
    sample_rate = meta.get("sample_rate_hz") or 22.0
    quality_map: list[list] = []
    for lap_df, classification, is_invalid, is_last in classified:
        warnings = validate_lap(lap_df, sample_rate=sample_rate, is_last=is_last)
        # position_jump → also set is_invalid on this lap
        has_position_jump = any(w.warning_type == "position_jump" for w in warnings)
        quality_map.append((warnings, has_position_jump))

    # Steps 6–7: Build setup entries and prepare for association
    setups = _build_setup_entries(meta)

    # Step 8: Corner detection
    corner_thresholds = compute_session_thresholds(df, sample_rate)
    # Select reference lap: first flying lap, else first outlap, else skip
    reference_lap_df: pd.DataFrame | None = None
    for lap_df, classification, _, _ in classified:
        if classification == "flying":
            reference_lap_df = lap_df
            break
    if reference_lap_df is None:
        for lap_df, classification, _, _ in classified:
            if classification == "outlap":
                reference_lap_df = lap_df
                break
    reference_apexes: list[float] = []
    if reference_lap_df is not None:
        reference_apexes = build_reference_map(reference_lap_df, corner_thresholds, sample_rate)

    # Step 9: Assemble Pydantic models
    session_metadata = _build_session_metadata(meta, df)

    laps: list[LapSegment] = []
    for (lap_df, classification, is_invalid, is_last), (warnings, has_position_jump) in zip(
        classified, quality_map
    ):
        if lap_df.empty:
            continue

        # position_jump anomaly promotes is_invalid
        effective_invalid = is_invalid or has_position_jump

        lap_number = int(lap_df["lap_count"].iloc[0])
        start_ts = float(lap_df["timestamp"].iloc[0]) if "timestamp" in lap_df.columns else 0.0
        end_ts = float(lap_df["timestamp"].iloc[-1]) if "timestamp" in lap_df.columns else 0.0
        start_norm = float(lap_df["normalized_position"].iloc[0])
        end_norm = float(lap_df["normalized_position"].iloc[-1])

        active_setup = associate_setup(lap_number, setups)

        corners = detect_corners(lap_df, reference_apexes, corner_thresholds, sample_rate)

        laps.append(LapSegment(
            lap_number=lap_number,
            classification=classification,
            is_invalid=effective_invalid,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            start_norm_pos=start_norm,
            end_norm_pos=end_norm,
            sample_count=len(lap_df),
            data=_df_to_data_dict(lap_df),
            corners=corners,
            active_setup=active_setup,
            quality_warnings=warnings,
        ))

    return ParsedSession(
        metadata=session_metadata,
        setups=setups,
        laps=laps,
    )
