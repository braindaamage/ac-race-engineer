"""Shared fixtures for parser tests.

All fixture data is generated programmatically — no game installation required.
Each session fixture returns a (csv_path, meta_path) tuple of tmp file paths.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Channel list (82 columns, matching ac_app/ac_race_engineer/modules/channels.py)
# ---------------------------------------------------------------------------

CHANNELS = [
    "timestamp", "session_time_ms", "normalized_position", "lap_count",
    "lap_time_ms", "throttle", "brake", "steering", "gear", "clutch",
    "handbrake", "speed_kmh", "rpm", "g_lat", "g_lon", "g_vert",
    "yaw_rate", "local_vel_x", "local_vel_y", "local_vel_z",
    "tyre_temp_core_fl", "tyre_temp_core_fr", "tyre_temp_core_rl", "tyre_temp_core_rr",
    "tyre_temp_inner_fl", "tyre_temp_inner_fr", "tyre_temp_inner_rl", "tyre_temp_inner_rr",
    "tyre_temp_mid_fl", "tyre_temp_mid_fr", "tyre_temp_mid_rl", "tyre_temp_mid_rr",
    "tyre_temp_outer_fl", "tyre_temp_outer_fr", "tyre_temp_outer_rl", "tyre_temp_outer_rr",
    "tyre_pressure_fl", "tyre_pressure_fr", "tyre_pressure_rl", "tyre_pressure_rr",
    "slip_angle_fl", "slip_angle_fr", "slip_angle_rl", "slip_angle_rr",
    "slip_ratio_fl", "slip_ratio_fr", "slip_ratio_rl", "slip_ratio_rr",
    "tyre_wear_fl", "tyre_wear_fr", "tyre_wear_rl", "tyre_wear_rr",
    "tyre_dirty_fl", "tyre_dirty_fr", "tyre_dirty_rl", "tyre_dirty_rr",
    "wheel_speed_fl", "wheel_speed_fr", "wheel_speed_rl", "wheel_speed_rr",
    "susp_travel_fl", "susp_travel_fr", "susp_travel_rl", "susp_travel_rr",
    "wheel_load_fl", "wheel_load_fr", "wheel_load_rl", "wheel_load_rr",
    "world_pos_x", "world_pos_y", "world_pos_z",
    "turbo_boost", "drs", "ers_charge", "fuel",
    "damage_front", "damage_rear", "damage_left", "damage_right", "damage_center",
    "in_pit_lane", "lap_invalid",
]

assert len(CHANNELS) == 82, f"Expected 82 channels, got {len(CHANNELS)}"

# Channels that are NaN in reduced mode
SIM_INFO_CHANNELS = [
    "tyre_temp_inner_fl", "tyre_temp_inner_fr", "tyre_temp_inner_rl", "tyre_temp_inner_rr",
    "tyre_temp_mid_fl", "tyre_temp_mid_fr", "tyre_temp_mid_rl", "tyre_temp_mid_rr",
    "tyre_temp_outer_fl", "tyre_temp_outer_fr", "tyre_temp_outer_rl", "tyre_temp_outer_rr",
    "tyre_wear_fl", "tyre_wear_fr", "tyre_wear_rl", "tyre_wear_rr",
    "wheel_load_fl", "wheel_load_fr", "wheel_load_rl", "wheel_load_rr",
    "drs", "ers_charge", "fuel",
    "damage_front", "damage_rear", "damage_left", "damage_right", "damage_center",
]

SAMPLE_RATE = 22.0  # Hz
SAMPLE_INTERVAL = 1.0 / SAMPLE_RATE
BASE_TIMESTAMP = 1_740_000_000.0


# ---------------------------------------------------------------------------
# Helper: build a lap's worth of rows
# ---------------------------------------------------------------------------

def _make_lap_rows(
    lap_number: int,
    n_samples: int,
    start_norm_pos: float = 0.0,
    end_norm_pos: float = 0.99,
    in_pit_start: int = 0,
    in_pit_end: int = 0,
    in_pit_mid: bool = False,
    lap_invalid_flag: bool = False,
    base_ts: float = 0.0,
    speed_profile: list[float] | None = None,
    g_lat_profile: list[float] | None = None,
    reduced_mode: bool = False,
) -> pd.DataFrame:
    """Generate a synthetic DataFrame for one lap segment."""
    rows = n_samples
    ts = base_ts + np.arange(rows) * SAMPLE_INTERVAL
    norm_pos = np.linspace(start_norm_pos, end_norm_pos, rows)

    speed = np.array(speed_profile) if speed_profile else np.full(rows, 120.0)
    g_lat = np.array(g_lat_profile) if g_lat_profile else np.zeros(rows)

    in_pit = np.zeros(rows, dtype=float)
    if in_pit_start:
        in_pit[0] = 1
    if in_pit_end:
        in_pit[-1] = 1
    if in_pit_mid:
        mid = rows // 2
        in_pit[mid : mid + 5] = 1

    lap_inv = np.ones(rows, dtype=float) if lap_invalid_flag else np.zeros(rows, dtype=float)

    data = {
        "timestamp": ts,
        "session_time_ms": ts * 1000 - BASE_TIMESTAMP * 1000,
        "normalized_position": norm_pos,
        "lap_count": float(lap_number),
        "lap_time_ms": np.arange(rows) * SAMPLE_INTERVAL * 1000,
        "throttle": np.full(rows, 0.5),
        "brake": np.zeros(rows),
        "steering": g_lat * 10,  # rough correlation
        "gear": np.full(rows, 3.0),
        "clutch": np.zeros(rows),
        "handbrake": np.full(rows, float("nan")),
        "speed_kmh": speed,
        "rpm": np.full(rows, 6000.0),
        "g_lat": g_lat,
        "g_lon": np.zeros(rows),
        "g_vert": np.ones(rows),
        "yaw_rate": np.zeros(rows),
        "local_vel_x": np.zeros(rows),
        "local_vel_y": np.full(rows, 33.0),
        "local_vel_z": np.zeros(rows),
        "tyre_temp_core_fl": np.full(rows, 80.0),
        "tyre_temp_core_fr": np.full(rows, 80.0),
        "tyre_temp_core_rl": np.full(rows, 78.0),
        "tyre_temp_core_rr": np.full(rows, 78.0),
        "tyre_temp_inner_fl": np.full(rows, float("nan") if reduced_mode else 85.0),
        "tyre_temp_inner_fr": np.full(rows, float("nan") if reduced_mode else 85.0),
        "tyre_temp_inner_rl": np.full(rows, float("nan") if reduced_mode else 83.0),
        "tyre_temp_inner_rr": np.full(rows, float("nan") if reduced_mode else 83.0),
        "tyre_temp_mid_fl": np.full(rows, float("nan") if reduced_mode else 82.0),
        "tyre_temp_mid_fr": np.full(rows, float("nan") if reduced_mode else 82.0),
        "tyre_temp_mid_rl": np.full(rows, float("nan") if reduced_mode else 80.0),
        "tyre_temp_mid_rr": np.full(rows, float("nan") if reduced_mode else 80.0),
        "tyre_temp_outer_fl": np.full(rows, float("nan") if reduced_mode else 79.0),
        "tyre_temp_outer_fr": np.full(rows, float("nan") if reduced_mode else 79.0),
        "tyre_temp_outer_rl": np.full(rows, float("nan") if reduced_mode else 77.0),
        "tyre_temp_outer_rr": np.full(rows, float("nan") if reduced_mode else 77.0),
        "tyre_pressure_fl": np.full(rows, 27.5),
        "tyre_pressure_fr": np.full(rows, 27.5),
        "tyre_pressure_rl": np.full(rows, 26.0),
        "tyre_pressure_rr": np.full(rows, 26.0),
        "slip_angle_fl": np.zeros(rows),
        "slip_angle_fr": np.zeros(rows),
        "slip_angle_rl": np.zeros(rows),
        "slip_angle_rr": np.zeros(rows),
        "slip_ratio_fl": np.zeros(rows),
        "slip_ratio_fr": np.zeros(rows),
        "slip_ratio_rl": np.zeros(rows),
        "slip_ratio_rr": np.zeros(rows),
        "tyre_wear_fl": np.full(rows, float("nan") if reduced_mode else 0.95),
        "tyre_wear_fr": np.full(rows, float("nan") if reduced_mode else 0.95),
        "tyre_wear_rl": np.full(rows, float("nan") if reduced_mode else 0.95),
        "tyre_wear_rr": np.full(rows, float("nan") if reduced_mode else 0.95),
        "tyre_dirty_fl": np.zeros(rows),
        "tyre_dirty_fr": np.zeros(rows),
        "tyre_dirty_rl": np.zeros(rows),
        "tyre_dirty_rr": np.zeros(rows),
        "wheel_speed_fl": np.full(rows, 200.0),
        "wheel_speed_fr": np.full(rows, 200.0),
        "wheel_speed_rl": np.full(rows, 195.0),
        "wheel_speed_rr": np.full(rows, 195.0),
        "susp_travel_fl": np.zeros(rows),
        "susp_travel_fr": np.zeros(rows),
        "susp_travel_rl": np.zeros(rows),
        "susp_travel_rr": np.zeros(rows),
        "wheel_load_fl": np.full(rows, float("nan") if reduced_mode else 3000.0),
        "wheel_load_fr": np.full(rows, float("nan") if reduced_mode else 3000.0),
        "wheel_load_rl": np.full(rows, float("nan") if reduced_mode else 3200.0),
        "wheel_load_rr": np.full(rows, float("nan") if reduced_mode else 3200.0),
        "world_pos_x": np.linspace(0, 100, rows),
        "world_pos_y": np.zeros(rows),
        "world_pos_z": np.linspace(0, 100, rows),
        "turbo_boost": np.zeros(rows),
        "drs": np.full(rows, float("nan") if reduced_mode else 0.0),
        "ers_charge": np.full(rows, float("nan") if reduced_mode else 0.0),
        "fuel": np.full(rows, float("nan") if reduced_mode else 50.0),
        "damage_front": np.full(rows, float("nan") if reduced_mode else 0.0),
        "damage_rear": np.full(rows, float("nan") if reduced_mode else 0.0),
        "damage_left": np.full(rows, float("nan") if reduced_mode else 0.0),
        "damage_right": np.full(rows, float("nan") if reduced_mode else 0.0),
        "damage_center": np.full(rows, float("nan") if reduced_mode else 0.0),
        "in_pit_lane": in_pit,
        "lap_invalid": lap_inv,
    }

    return pd.DataFrame(data)[CHANNELS]


# ---------------------------------------------------------------------------
# Public fixture builder functions
# ---------------------------------------------------------------------------

def make_session_df(lap_configs: list[dict]) -> pd.DataFrame:
    """Build a session DataFrame from a list of lap config dicts.

    Each dict accepts: lap_number, n_samples, in_pit_start, in_pit_end,
    in_pit_mid, lap_invalid_flag, speed_profile, g_lat_profile, reduced_mode.
    Timestamps are sequential across laps.
    """
    frames = []
    ts_offset = BASE_TIMESTAMP
    for cfg in lap_configs:
        n = cfg.get("n_samples", 500)
        lap_df = _make_lap_rows(
            lap_number=cfg["lap_number"],
            n_samples=n,
            start_norm_pos=cfg.get("start_norm_pos", 0.0),
            end_norm_pos=cfg.get("end_norm_pos", 0.99),
            in_pit_start=cfg.get("in_pit_start", 0),
            in_pit_end=cfg.get("in_pit_end", 0),
            in_pit_mid=cfg.get("in_pit_mid", False),
            lap_invalid_flag=cfg.get("lap_invalid_flag", False),
            base_ts=ts_offset,
            speed_profile=cfg.get("speed_profile"),
            g_lat_profile=cfg.get("g_lat_profile"),
            reduced_mode=cfg.get("reduced_mode", False),
        )
        frames.append(lap_df)
        ts_offset += n * SAMPLE_INTERVAL
    if not frames:
        return pd.DataFrame(columns=CHANNELS)
    return pd.concat(frames, ignore_index=True)


def make_metadata_v2(overrides: dict | None = None) -> dict:
    """Build a v2.0 metadata dict with sensible defaults."""
    base: dict[str, Any] = {
        "app_version": "0.2.0",
        "session_start": "2026-03-02T14:30:00",
        "session_end": "2026-03-02T15:00:00",
        "car_name": "ks_ferrari_488_gt3",
        "track_name": "monza",
        "track_config": "",
        "track_length_m": 5793.0,
        "session_type": "practice",
        "tyre_compound": "DHF",
        "laps_completed": 3,
        "total_samples": 1500,
        "sample_rate_hz": SAMPLE_RATE,
        "air_temp_c": 22.0,
        "road_temp_c": 30.5,
        "driver_name": "Test Driver",
        "setup_history": [
            {
                "timestamp": "2026-03-02T14:30:00",
                "trigger": "session_start",
                "lap": 0,
                "filename": "test_setup.ini",
                "contents": "[FRONT]\nCAMBER=-2.5\nTOE=0.1\n\n[REAR]\nCAMBER=-1.8\nTOE=0.05\n",
                "confidence": "high",
            }
        ],
        "channels_available": [c for c in CHANNELS if c != "handbrake"],
        "channels_unavailable": ["handbrake"],
        "sim_info_available": True,
        "reduced_mode": False,
        "tyre_temp_zones_validated": True,
        "csv_filename": "2026-03-02_1430_ks_ferrari_488_gt3_monza.csv",
    }
    if overrides:
        base.update(overrides)
    return base


def make_metadata_v1_legacy() -> dict:
    """Build a v1.0 metadata dict (flat setup fields, no setup_history key)."""
    return {
        "app_version": "0.1.0",
        "session_start": "2026-01-15T10:00:00",
        "session_end": "2026-01-15T10:30:00",
        "car_name": "ks_ferrari_488_gt3",
        "track_name": "monza",
        "track_config": "",
        "track_length_m": 5793.0,
        "session_type": "practice",
        "tyre_compound": "DHF",
        "laps_completed": 2,
        "total_samples": 1000,
        "sample_rate_hz": SAMPLE_RATE,
        "air_temp_c": 20.0,
        "road_temp_c": 28.0,
        "driver_name": "Legacy Driver",
        "setup_filename": "legacy_setup.ini",
        "setup_contents": "[FRONT]\nCAMBER=-3.0\n\n[REAR]\nCAMBER=-2.0\n",
        "setup_confidence": "medium",
        "channels_available": [c for c in CHANNELS if c != "handbrake"],
        "channels_unavailable": ["handbrake"],
        "sim_info_available": True,
        "reduced_mode": False,
        "csv_filename": "2026-01-15_1000_ks_ferrari_488_gt3_monza.csv",
    }


# ---------------------------------------------------------------------------
# CSV + meta.json writer helpers
# ---------------------------------------------------------------------------

def _write_session_files(
    tmp_path: Path,
    df: pd.DataFrame,
    meta: dict,
    name: str = "session",
) -> tuple[Path, Path]:
    """Write DataFrame to CSV and meta dict to .meta.json, return paths."""
    csv_path = tmp_path / f"{name}.csv"
    meta_path = tmp_path / f"{name}.meta.json"
    df.to_csv(csv_path, index=False)
    meta["csv_filename"] = csv_path.name
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return csv_path, meta_path


# ---------------------------------------------------------------------------
# Named pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_session_files(tmp_path):
    """1 outlap + 1 flying lap + 1 inlap — clean data."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "in_pit_start": 1},   # outlap
        {"lap_number": 1, "n_samples": 500},                       # flying
        {"lap_number": 2, "n_samples": 300, "in_pit_end": 1},      # inlap
    ])
    meta = make_metadata_v2({"laps_completed": 3, "total_samples": len(df)})
    return _write_session_files(tmp_path, df, meta, "minimal_session")


@pytest.fixture
def zero_laps_files(tmp_path):
    """Driver quit immediately — only a handful of samples, no lap_count transition."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 10},
    ])
    meta = make_metadata_v2({"laps_completed": 0, "total_samples": len(df)})
    return _write_session_files(tmp_path, df, meta, "zero_laps")


@pytest.fixture
def crash_session_files(tmp_path):
    """session_end, laps_completed, total_samples all null — game crashed."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "in_pit_start": 1},
        {"lap_number": 1, "n_samples": 200},  # crashed mid lap
    ])
    meta = make_metadata_v2({
        "session_end": None,
        "laps_completed": None,
        "total_samples": None,
        "sample_rate_hz": None,
        "total_samples": None,
    })
    meta["total_samples"] = None
    return _write_session_files(tmp_path, df, meta, "crash_session")


@pytest.fixture
def legacy_v1_files(tmp_path):
    """v1.0 metadata — flat setup fields instead of setup_history."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "in_pit_start": 1},
        {"lap_number": 1, "n_samples": 500},
    ])
    meta = make_metadata_v1_legacy()
    meta["laps_completed"] = 2
    meta["total_samples"] = len(df)
    return _write_session_files(tmp_path, df, meta, "legacy_v1")


@pytest.fixture
def all_invalid_files(tmp_path):
    """All laps have lap_invalid==1."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "lap_invalid_flag": True},
        {"lap_number": 1, "n_samples": 500, "lap_invalid_flag": True},
    ])
    meta = make_metadata_v2({"laps_completed": 2, "total_samples": len(df)})
    return _write_session_files(tmp_path, df, meta, "all_invalid")


@pytest.fixture
def reduced_mode_files(tmp_path):
    """28 sim_info channels all NaN."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "in_pit_start": 1, "reduced_mode": True},
        {"lap_number": 1, "n_samples": 500, "reduced_mode": True},
    ])
    meta = make_metadata_v2({
        "sim_info_available": False,
        "reduced_mode": True,
        "channels_available": [c for c in CHANNELS if c not in SIM_INFO_CHANNELS and c != "handbrake"],
        "channels_unavailable": SIM_INFO_CHANNELS + ["handbrake"],
        "laps_completed": 2,
        "total_samples": len(df),
    })
    return _write_session_files(tmp_path, df, meta, "reduced_mode")


@pytest.fixture
def multi_setup_files(tmp_path):
    """3 setup changes at laps 1, 6, 12 — 15 laps total."""
    lap_configs = []
    for i in range(15):
        cfg: dict[str, Any] = {"lap_number": i, "n_samples": 300}
        if i == 0:
            cfg["in_pit_start"] = 1
        if i == 14:
            cfg["in_pit_end"] = 1
        lap_configs.append(cfg)
    df = make_session_df(lap_configs)
    meta = make_metadata_v2({
        "laps_completed": 15,
        "total_samples": len(df),
        "setup_history": [
            {
                "timestamp": "2026-03-02T14:30:00",
                "trigger": "session_start",
                "lap": 0,
                "filename": "setup_a.ini",
                "contents": "[FRONT]\nCAMBER=-2.5\n",
                "confidence": "high",
            },
            {
                "timestamp": "2026-03-02T14:40:00",
                "trigger": "pit_exit",
                "lap": 6,
                "filename": "setup_b.ini",
                "contents": "[FRONT]\nCAMBER=-3.0\n",
                "confidence": "high",
            },
            {
                "timestamp": "2026-03-02T14:50:00",
                "trigger": "pit_exit",
                "lap": 12,
                "filename": "setup_c.ini",
                "contents": "[FRONT]\nCAMBER=-2.0\n",
                "confidence": "high",
            },
        ],
    })
    return _write_session_files(tmp_path, df, meta, "multi_setup")


@pytest.fixture
def data_gaps_files(tmp_path):
    """Intentional time gap (>0.5s) and position jump (>0.05) inserted."""
    df = make_session_df([
        {"lap_number": 0, "n_samples": 500, "in_pit_start": 1},
        {"lap_number": 1, "n_samples": 500},
    ])
    # Inject a 1-second gap in lap 1 (at sample index ~550)
    gap_idx = 550
    df.loc[gap_idx, "timestamp"] = df.loc[gap_idx - 1, "timestamp"] + 1.2
    # Inject a position jump (>0.05) at sample ~600
    jump_idx = 600
    df.loc[jump_idx, "normalized_position"] = df.loc[jump_idx - 1, "normalized_position"] + 0.10

    meta = make_metadata_v2({"laps_completed": 2, "total_samples": len(df)})
    return _write_session_files(tmp_path, df, meta, "data_gaps")
