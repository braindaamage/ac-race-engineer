# API Contract: Analysis Endpoints

**Feature**: 012-analysis-endpoints | **Date**: 2026-03-05

All endpoints are nested under the existing `/sessions/{session_id}` path. The session_id is the string identifier stored in SQLite.

---

## POST /sessions/{session_id}/process

Trigger the parse+analyze pipeline for a session.

**Request**: No body.

**Response 202 Accepted**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza"
}
```

**Error 404**: Session not found.
```json
{
  "error": {
    "type": "not_found",
    "message": "Session not found: {session_id}"
  }
}
```

**Error 409**: Job already running for this session.
```json
{
  "error": {
    "type": "conflict",
    "message": "Processing already in progress for session: {session_id}"
  }
}
```

**Job Progress** (via WebSocket `/ws/jobs/{job_id}`):
```json
{"event": "progress", "job_id": "...", "status": "running", "progress": 40, "current_step": "Analyzing metrics..."}
```

**Job Completion**:
```json
{"event": "completed", "job_id": "...", "status": "completed", "progress": 100, "result": {"session_id": "...", "state": "analyzed"}}
```

**Job Failure**:
```json
{"event": "failed", "job_id": "...", "status": "failed", "error": "CSV file not found: /path/to/session.csv"}
```

---

## GET /sessions/{session_id}/laps

List all laps with summary metrics.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "lap_count": 12,
  "laps": [
    {
      "lap_number": 0,
      "classification": "outlap",
      "is_invalid": false,
      "lap_time_s": 95.432,
      "tyre_temps_avg": {"fl": 80.0, "fr": 80.0, "rl": 78.0, "rr": 78.0},
      "peak_lat_g": 1.8,
      "peak_lon_g": 1.2,
      "full_throttle_pct": 0.65,
      "braking_pct": 0.18
    }
  ]
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet.
```json
{
  "error": {
    "type": "conflict",
    "message": "Session has not been analyzed yet. Current state: discovered. Process the session first."
  }
}
```

---

## GET /sessions/{session_id}/laps/{lap_number}

Full detailed metrics for a single lap.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "lap_number": 1,
  "classification": "flying",
  "is_invalid": false,
  "metrics": {
    "timing": {"lap_time_s": 92.1, "sector_times_s": null},
    "tyres": {"temps_avg": {"fl": {"core": 80, "inner": 85, "mid": 82, "outer": 79}, ...}, ...},
    "grip": {"slip_angle_avg": {"fl": 0.04, ...}, "peak_lat_g": 1.8, ...},
    "driver_inputs": {"full_throttle_pct": 0.72, "braking_pct": 0.15, ...},
    "speed": {"max_speed": 245.0, "min_speed": 55.0, "avg_speed": 148.0},
    "fuel": {"fuel_start": 50.0, "fuel_end": 48.2, "consumption": 1.8},
    "suspension": {"travel_avg": {"fl": 0.05, ...}, ...}
  }
}
```

**Error 404**: Session not found, or lap_number does not exist in session.
**Error 409**: Session not analyzed yet.

---

## GET /sessions/{session_id}/corners

All corners with aggregated metrics across flying laps.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "corner_count": 15,
  "corners": [
    {
      "corner_number": 1,
      "sample_count": 8,
      "avg_apex_speed_kmh": 95.2,
      "avg_entry_speed_kmh": 180.5,
      "avg_exit_speed_kmh": 120.3,
      "avg_duration_s": 3.2,
      "avg_understeer_ratio": 0.15,
      "avg_trail_braking_intensity": 0.42,
      "avg_peak_lat_g": 1.6
    }
  ]
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet.

---

## GET /sessions/{session_id}/corners/{corner_number}

Per-lap metrics for a specific corner.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "corner_number": 1,
  "laps": [
    {
      "lap_number": 1,
      "metrics": {
        "corner_number": 1,
        "performance": {"entry_speed_kmh": 182.0, "apex_speed_kmh": 96.0, "exit_speed_kmh": 121.0, "duration_s": 3.1},
        "grip": {"peak_lat_g": 1.65, "avg_lat_g": 1.2, "understeer_ratio": 0.14},
        "technique": {"brake_point_norm": 0.08, "throttle_on_norm": 0.17, "trail_braking_intensity": 0.45},
        "loading": null
      }
    }
  ]
}
```

**Error 404**: Session not found, or corner_number does not exist.
**Error 409**: Session not analyzed yet.

---

## GET /sessions/{session_id}/stints

All stints with aggregated metrics and trends.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "stint_count": 2,
  "stints": [
    {
      "stint_index": 0,
      "setup_filename": "setup_a.ini",
      "lap_numbers": [1, 2, 3, 4],
      "flying_lap_count": 3,
      "aggregated": {
        "lap_time_mean_s": 93.5,
        "lap_time_stddev_s": 0.8,
        "tyre_temp_avg": {"fl": 82.0, "fr": 82.5, "rl": 80.0, "rr": 80.5},
        "slip_angle_avg": {"fl": 0.04, "fr": 0.04, "rl": 0.05, "rr": 0.05},
        "slip_ratio_avg": {"fl": 0.02, "fr": 0.02, "rl": 0.025, "rr": 0.025},
        "peak_lat_g_avg": 1.7
      },
      "trends": {
        "lap_time_slope": 0.15,
        "tyre_temp_slope": {"fl": 0.3, "fr": 0.3, "rl": 0.2, "rr": 0.2},
        "fuel_consumption_slope": -0.01
      }
    }
  ]
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet.

---

## GET /sessions/{session_id}/compare?stint_a={a}&stint_b={b}

Compare two stints by index.

**Query Parameters**:
- `stint_a` (int, required): Index of the first stint.
- `stint_b` (int, required): Index of the second stint.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "comparison": {
    "stint_a_index": 0,
    "stint_b_index": 1,
    "setup_changes": [
      {"section": "FRONT", "name": "CAMBER", "value_a": -2.5, "value_b": -3.0}
    ],
    "metric_deltas": {
      "lap_time_delta_s": -0.8,
      "tyre_temp_delta": {"fl": 2.0, "fr": 2.5, "rl": 1.5, "rr": 1.5},
      "slip_angle_delta": {},
      "slip_ratio_delta": {},
      "peak_lat_g_delta": 0.1
    }
  }
}
```

**Error 404**: Session not found, or stint index does not exist.
**Error 409**: Session not analyzed yet.
**Error 422**: Missing required query parameters.

---

## GET /sessions/{session_id}/consistency

Session-wide consistency metrics.

**Response 200**:
```json
{
  "session_id": "2026-03-02_1430_ks_ferrari_488_gt3_monza",
  "consistency": {
    "flying_lap_count": 8,
    "lap_time_stddev_s": 0.65,
    "best_lap_time_s": 91.8,
    "worst_lap_time_s": 94.2,
    "lap_time_trend_slope": 0.05,
    "corner_consistency": [
      {
        "corner_number": 1,
        "apex_speed_variance": 4.5,
        "apex_speed_stddev": 2.12,
        "brake_point_variance": 0.002,
        "sample_count": 8
      }
    ]
  }
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet.

---

## Common Error Format

All errors follow the uniform error envelope from Phase 6.1:

```json
{
  "error": {
    "type": "not_found | conflict | validation_error",
    "message": "Human-readable description",
    "detail": null
  }
}
```

## Common Guard Rails

All metric GET endpoints (`/laps`, `/laps/{n}`, `/corners`, `/corners/{n}`, `/stints`, `/compare`, `/consistency`) share these guards:

1. **Session existence**: `get_session(db_path, session_id)` — 404 if None
2. **Session state**: Check `session.state` is "analyzed" or "engineered" — 409 if not
3. **Cache existence**: `load_analyzed_session(cache_dir)` — 409 with "re-process" message if cache missing or corrupted
