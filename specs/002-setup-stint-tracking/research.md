# Research: Setup Stint Tracking

**Feature**: 002-setup-stint-tracking
**Date**: 2026-03-03

## R-001: Confidence Scoring Revision

**Decision**: Replace timestamp-threshold confidence scoring with location-first scoring. Track-specific directory + 1 file → `"high"`. Track-specific directory + multiple files → `"medium"`. Generic car directory (any count) → `"low"`. Modification timestamp is retained only as a **sort key** when selecting the most recent file among multiple candidates in the same directory.

**Rationale**: AC does not reliably update a setup file's modification time when the user loads it. The game may load from an in-memory cache without touching the file. As a result, a setup file loaded at session start may show an mtime of days or weeks ago. Using a 60-second threshold to grant `"high"` confidence therefore excludes the majority of legitimate track-specific setups.

Directory location, by contrast, is a deliberately chosen signal: a file saved to `setups/{car}/{track}/` was placed there specifically for that car-track combination. A file in `setups/{car}/` is a fallback with no track-specific intent. This is a more reliable indicator than a wall-clock threshold.

The number of files in the directory remains meaningful: one file means there is no ambiguity about which setup is active. Multiple files means the selection is a best-effort guess using recency.

**Current scoring logic (to be replaced)**:
```
track-specific + 1 file + age ≤ 60s  → "high"
track-specific + age ≤ 600s           → "medium"
track-specific + age > 600s           → "low"  ← bug
generic                               → "low"
```

**New scoring logic**:
```
track-specific + 1 file   → "high"
track-specific + N files  → "medium"  (most recent selected as best guess)
generic (any count)       → "low"
```

**Alternatives considered**:
- Add a "very low" tier for generic + old timestamp → rejected (oversegmenting; the generic/track-specific distinction is already the meaningful boundary).
- Read the AC log file to find which setup was explicitly loaded → rejected (AC log format is undocumented and varies by version; too fragile).
- Ask the driver to confirm the setup after session start → rejected (violates zero-interaction principle from spec 001 SC-008).

---

## R-002: Pit Exit Detection Mechanism

**Decision**: Detect pit exits via a frame-to-frame boolean transition on `ac.isCarInPitlane(0)`. In each `acUpdate()` call during `STATE_RECORDING`, compare the current pit-lane status with the value from the previous frame. A transition from `True` → `False` is a pit exit and triggers a setup re-read.

**Rationale**: AC exposes no "pit exit" callback or event. The `in_pit_lane` channel is already being written to the CSV (as `in_pit_lane` — an existing channel), confirming `ac.isCarInPitlane(0)` is available and reliable in both normal and reduced modes. Frame-diff is the standard pattern used throughout the session manager for all other transition detection (e.g., session status changes).

The `_was_in_pitlane` boolean is tracked in module-level state (`ac_race_engineer.py`) and reset to `False` when recording starts. This ensures a cold start (car already in pit) doesn't fire a false pit exit on the first frame where the car crosses the pit exit line.

**No debounce needed**: The pit lane entry/exit boundary is a physical line; `isCarInPitlane` changes exactly once per crossing in practice. Unlike session status changes which can flicker, pit lane status is clean. A multi-frame confirmation window would only delay legitimate capture.

**Fallback mode**: `ac.isCarInPitlane(0)` is an `ac` module function, not a `sim_info` field. It is available in both normal and reduced (fallback) modes.

**Alternatives considered**:
- Poll the setup file's mtime and re-read on any change → rejected (mtime is unreliable per R-001; we'd be building on a known-broken signal).
- Use `sim_info.graphics.isInPit` or similar field → no such field exists in AC's shared memory struct. `ac.isCarInPitlane()` is the correct API.
- Periodic re-read every N seconds → rejected (would produce false "changes" between stints when no setup change occurred; adds noise).

---

## R-003: Mid-Session Metadata Persistence

**Decision**: Reuse `write_early_metadata(filepath, metadata_dict)` to update the on-disk metadata file when a new setup history entry is appended during the session. This function already writes all known metadata with the four deferred fields (`session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`) forced to `null`, which is the correct state mid-session.

**Rationale**: The existing `write_early_metadata` implementation produces exactly the right output for mid-session writes: all session context is captured, deferred fields are explicitly null (so crash detection still works), and `setup_history` is written as part of `_session_metadata`. No new writer function is needed.

**Write cadence with this feature**:
1. Session start: `write_early_metadata` (unchanged)
2. Per pit exit with change: `write_early_metadata` again (new, this feature)
3. Session end: `write_final_metadata` (unchanged)

Each write is a complete overwrite of the `.meta.json` file, so there is no append or patch logic — the entire current state is serialized. This is safe because `json.dump` with a temp-and-rename strategy would be ideal for atomicity, but given AC's single-threaded execution model and the rarity of pit exits, direct overwrite is acceptable. There is no concurrent writer.

**Performance**: Each mid-session metadata write serializes ~1-5 KB of JSON. At pit exit frequency (typically 0-4 times per race session), the I/O cost is negligible compared to the periodic CSV flushes (~400 KB every 30 seconds).

**Alternatives considered**:
- Append a JSON line to a separate setup-changes file → rejected (adds a third per-session file, complicates downstream consumers, splits what should be one cohesive metadata record).
- Add a new `write_mid_session_metadata` function → rejected (identical to `write_early_metadata`; DRY).
- Queue the write for the next CSV flush → rejected (creates a window where a crash loses the pit exit setup entry; FR-010 requires the write in the same frame cycle).

---

## R-004: Setup History Schema

**Decision**: Replace the three flat top-level fields (`setup_filename`, `setup_contents`, `setup_confidence`) with a single `setup_history` field containing an ordered list of setup capture entries. Each entry has: `timestamp` (ISO 8601 string), `trigger` ("session_start" | "pit_exit"), `lap` (int), `filename` (string | null), `contents` (string | null), `confidence` ("high" | "medium" | "low" | null).

**Rationale**: A list is the natural representation of an ordered timeline. Downstream consumers (Phase 2 parser, Phase 5 AI) need to answer "what setup was active at lap N?" — this is trivially answered by iterating `setup_history` in reverse to find the latest entry where `entry["lap"] <= N`. A flat single-value structure requires awkward workarounds or parallel arrays.

The decision to make this a **breaking change** (removing the flat fields) rather than an additive change (keeping flat fields + adding history) is deliberate: adding both would create two conflicting sources of truth. Since Phase 2 (the first consumer) has not yet been built, there is no migration cost.

**Lookup algorithm for downstream consumers**:
```python
def active_setup_at_lap(setup_history, lap):
    result = None
    for entry in setup_history:
        if entry["lap"] <= lap:
            result = entry
    return result  # Last entry with lap <= N
```

**Alternatives considered**:
- Keep flat fields + add `setup_history` in parallel → rejected (dual source of truth; flat fields can drift out of sync with history).
- Separate `setup_changes.json` file per session → rejected (adds a third file pair; setup context belongs with session metadata).
- Map keyed by lap number → rejected (JSON object keys must be strings; integer-keyed maps are awkward and unordered in Python 3.3).

---

## R-005: Content Comparison Strategy

**Decision**: Compare setup contents as raw strings read with `open(path, "r")` in text mode. If the full text of the newly read file differs from the `contents` field of the most recent setup history entry, append a new entry.

**Rationale**: Text mode read normalizes line endings (`\r\n` → `\n`) consistently across reads, so comparison is stable regardless of how AC writes the file. Two reads of the same unchanged file will always compare equal. Any substantive change to setup values (even a single parameter) will change the file text and trigger a new entry.

**Edge: setup changes filename but not content**: If the driver loads a different preset that happens to have identical parameter values, no new entry is added. This is acceptable — for AI analysis, what matters is the parameters, not the name.

**Edge: setup changes content but not filename**: A new entry IS added. This correctly handles iterative editing of the same file.

**Edge: first entry has `contents = null`** (setup file not found at session start): Any non-null contents at pit exit will produce a new entry (null ≠ string).

**Alternatives considered**:
- Hash-based comparison (MD5/SHA) → rejected (no `hashlib` in Python 3.3 without additional imports; raw string comparison is simpler and equally correct).
- Section-by-section INI parse and compare → rejected (over-engineering; raw text comparison is sufficient and avoids parsing edge cases).
- Filename comparison only → rejected (same filename can have different contents after editing; this would miss setup changes).

---

## R-006: Test Strategy

**Decision**: Update `test_setup_reader.py` to replace timestamp-based assertions with location-based assertions. Add a new `test_setup_history.py` for the pit exit detection and history accumulation logic extracted from `ac_race_engineer.py` into a testable helper function.

**Existing tests requiring changes**:

| Test | Current assertion | New assertion |
|---|---|---|
| `test_confidence_low_old_file` | Single file, age=700s → `"low"` | Single file, age=700s → `"high"` (single track-specific file is always high) |
| `test_confidence_high_single_recent` | Single file, age=10s → `"high"` | Unchanged (still correct) |

**New tests required**:
- `test_confidence_high_single_very_old`: Single file, age=48h → `"high"`
- `test_confidence_medium_old_multiple`: Two files, one very old → `"medium"` (not "low")
- `test_pit_exit_no_change`: Pit exit, same contents → no new history entry
- `test_pit_exit_with_change`: Pit exit, different contents → new entry added
- `test_pit_exit_unreadable_file`: Pit exit, file read fails → null entry added
- `test_history_initial_entry`: Session start always produces one entry
- `test_history_initial_null`: Session start with no setup file → null-content entry still present
