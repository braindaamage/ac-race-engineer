"""Parquet + JSON serialization for ParsedSession (save and load).

Provides a round-trip-identical intermediate cache format:
- telemetry.parquet: full time series, all laps, with lap_number column
- session.json: SessionMetadata + laps metadata + setups + corners + warnings
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ac_engineer.parser.models import (
    CornerSegment,
    LapSegment,
    ParsedSession,
    QualityWarning,
    SessionMetadata,
    SetupEntry,
    SetupParameter,
)

FORMAT_VERSION = "1.0"


def save_session(
    session: ParsedSession,
    output_dir: Path,
    base_name: str | None = None,
) -> Path:
    """Serialize a ParsedSession to Parquet + JSON format.

    Creates ``output_dir/<base_name>/`` containing:
    - ``telemetry.parquet``: all lap time-series data with ``lap_number`` column
    - ``session.json``: SessionMetadata, setups, and per-lap structured data

    Args:
        session: The ParsedSession to serialize.
        output_dir: Directory under which the session subdirectory is created.
        base_name: Optional subdirectory name. If None, derived from
            ``session.metadata.csv_filename`` (strip .csv extension).

    Returns:
        Path to the created session directory.

    Raises:
        OSError: If output_dir cannot be written to.
    """
    output_dir = Path(output_dir)

    if base_name is None:
        csv_name = session.metadata.csv_filename
        base_name = csv_name.replace(".csv", "") if csv_name else "session"

    session_dir = output_dir / base_name
    session_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Write telemetry.parquet — all laps concatenated with lap_number column
    # -----------------------------------------------------------------------
    frames = []
    for lap in session.laps:
        if not lap.data:
            continue
        lap_df = pd.DataFrame(lap.data)
        lap_df.insert(0, "lap_number", lap.lap_number)
        frames.append(lap_df)

    if frames:
        all_df = pd.concat(frames, ignore_index=True)
    else:
        all_df = pd.DataFrame({"lap_number": []})

    parquet_path = session_dir / "telemetry.parquet"
    all_df.to_parquet(parquet_path, index=False)

    # -----------------------------------------------------------------------
    # Build setups list for JSON (full SetupEntry serialization)
    # -----------------------------------------------------------------------
    setups_list = []
    for entry in session.setups:
        setups_list.append({
            "lap_start": entry.lap_start,
            "trigger": entry.trigger,
            "confidence": entry.confidence,
            "filename": entry.filename,
            "timestamp": entry.timestamp,
            "parameters": [
                {"section": p.section, "name": p.name, "value": p.value}
                for p in entry.parameters
            ],
        })

    # Build lookup: SetupEntry object → index in setups list
    setup_index_map: dict[int, int] = {}
    for idx, entry in enumerate(session.setups):
        setup_index_map[id(entry)] = idx

    # -----------------------------------------------------------------------
    # Build laps list (no data field; use active_setup_index)
    # -----------------------------------------------------------------------
    laps_list = []
    for lap in session.laps:
        active_setup_index: int | None = None
        if lap.active_setup is not None:
            active_setup_index = setup_index_map.get(id(lap.active_setup))
            # Fallback: match by lap_start if id lookup fails (e.g. after model copy)
            if active_setup_index is None:
                for idx, entry in enumerate(session.setups):
                    if entry.lap_start == lap.active_setup.lap_start:
                        active_setup_index = idx
                        break

        laps_list.append({
            "lap_number": lap.lap_number,
            "classification": lap.classification,
            "is_invalid": lap.is_invalid,
            "start_timestamp": lap.start_timestamp,
            "end_timestamp": lap.end_timestamp,
            "start_norm_pos": lap.start_norm_pos,
            "end_norm_pos": lap.end_norm_pos,
            "sample_count": lap.sample_count,
            "active_setup_index": active_setup_index,
            "corners": [
                {
                    "corner_number": c.corner_number,
                    "entry_norm_pos": c.entry_norm_pos,
                    "apex_norm_pos": c.apex_norm_pos,
                    "exit_norm_pos": c.exit_norm_pos,
                    "apex_speed_kmh": c.apex_speed_kmh,
                    "max_lat_g": c.max_lat_g,
                    "entry_speed_kmh": c.entry_speed_kmh,
                    "exit_speed_kmh": c.exit_speed_kmh,
                }
                for c in lap.corners
            ],
            "quality_warnings": [
                {
                    "warning_type": w.warning_type,
                    "normalized_position": w.normalized_position,
                    "description": w.description,
                }
                for w in lap.quality_warnings
            ],
        })

    session_json = {
        "format_version": FORMAT_VERSION,
        "session": session.metadata.model_dump(),
        "setups": setups_list,
        "laps": laps_list,
    }

    json_path = session_dir / "session.json"
    json_path.write_text(json.dumps(session_json, indent=2), encoding="utf-8")

    return session_dir


def load_session(session_dir: Path) -> ParsedSession:
    """Load a ParsedSession from a previously saved intermediate format.

    Reads ``telemetry.parquet`` and ``session.json`` and reconstructs the
    full ParsedSession structurally identical to the original.

    Args:
        session_dir: Path to the session directory (as returned by save_session).

    Returns:
        Fully reconstructed ParsedSession.

    Raises:
        FileNotFoundError: If session_dir, telemetry.parquet, or session.json missing.
        ValueError: If format_version in session.json is incompatible.
    """
    session_dir = Path(session_dir)

    if not session_dir.exists():
        raise FileNotFoundError(f"Session directory not found: {session_dir}")

    json_path = session_dir / "session.json"
    parquet_path = session_dir / "telemetry.parquet"

    if not json_path.exists():
        raise FileNotFoundError(f"session.json not found in: {session_dir}")
    if not parquet_path.exists():
        raise FileNotFoundError(f"telemetry.parquet not found in: {session_dir}")

    session_data = json.loads(json_path.read_text(encoding="utf-8"))

    version = session_data.get("format_version", "")
    if version != FORMAT_VERSION:
        raise ValueError(
            f"Incompatible format_version: {version!r} (expected {FORMAT_VERSION!r})"
        )

    # -----------------------------------------------------------------------
    # Reconstruct SessionMetadata
    # -----------------------------------------------------------------------
    metadata = SessionMetadata(**session_data["session"])

    # -----------------------------------------------------------------------
    # Reconstruct SetupEntry list
    # -----------------------------------------------------------------------
    setups: list[SetupEntry] = []
    for entry_dict in session_data.get("setups", []):
        parameters = [
            SetupParameter(**p) for p in entry_dict.get("parameters", [])
        ]
        setups.append(SetupEntry(
            lap_start=entry_dict["lap_start"],
            trigger=entry_dict["trigger"],
            confidence=entry_dict.get("confidence"),
            filename=entry_dict.get("filename"),
            timestamp=entry_dict["timestamp"],
            parameters=parameters,
        ))

    # -----------------------------------------------------------------------
    # Read Parquet — full time series
    # -----------------------------------------------------------------------
    all_df = pd.read_parquet(parquet_path)

    # -----------------------------------------------------------------------
    # Reconstruct LapSegment list
    # -----------------------------------------------------------------------
    laps: list[LapSegment] = []
    for lap_dict in session_data.get("laps", []):
        lap_number = lap_dict["lap_number"]

        # Extract per-lap time series
        lap_rows = all_df[all_df["lap_number"] == lap_number].drop(columns=["lap_number"])
        data: dict[str, list] = {}
        for col in lap_rows.columns:
            values = lap_rows[col].tolist()
            # Convert NaN → None for JSON compatibility
            data[col] = [None if (isinstance(v, float) and v != v) else v for v in values]

        # Resolve active_setup
        active_setup: SetupEntry | None = None
        setup_idx = lap_dict.get("active_setup_index")
        if setup_idx is not None and 0 <= setup_idx < len(setups):
            active_setup = setups[setup_idx]

        # Reconstruct corners
        corners = [CornerSegment(**c) for c in lap_dict.get("corners", [])]

        # Reconstruct quality warnings
        quality_warnings = [QualityWarning(**w) for w in lap_dict.get("quality_warnings", [])]

        laps.append(LapSegment(
            lap_number=lap_number,
            classification=lap_dict["classification"],
            is_invalid=lap_dict.get("is_invalid", False),
            start_timestamp=lap_dict["start_timestamp"],
            end_timestamp=lap_dict["end_timestamp"],
            start_norm_pos=lap_dict["start_norm_pos"],
            end_norm_pos=lap_dict["end_norm_pos"],
            sample_count=lap_dict["sample_count"],
            data=data,
            corners=corners,
            active_setup=active_setup,
            quality_warnings=quality_warnings,
        ))

    return ParsedSession(
        metadata=metadata,
        setups=setups,
        laps=laps,
    )
