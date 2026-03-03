# Research: Telemetry Capture App

**Feature**: 001-telemetry-capture
**Date**: 2026-03-02

## R-001: AC Python Runtime Compatibility

**Decision**: Target Python 3.3.5 syntax and stdlib exclusively for all in-game code.

**Rationale**: AC ships with `python33.dll` (Python 3.3.5, March 2014). This is non-upgradable without modifying the AC installation. All in-game code must be compatible.

**Key constraints**:
- No f-strings (3.6+) — use `"text %s" % var` or `"text {}".format(var)`
- No `pathlib` (3.4+) — use `os.path` exclusively
- No `enum` module (3.4+) — define constants as plain integers or class attributes
- No `typing` module (3.5+) — no type annotations in AC app code
- No `asyncio` (3.4+) — all code is synchronous
- `os.makedirs(path, exist_ok=True)` IS available (added in 3.2)
- `configparser` (lowercase) IS available (renamed from `ConfigParser` in 3.0)
- `csv`, `json`, `os`, `time`, `struct`, `io`, `collections`, `math`, `traceback`, `sys` — all available
- `ctypes` and `mmap` — available but `_ctypes.pyd` may need to be bundled

**Alternatives considered**:
- Require Content Manager / CSP Python upgrade → rejected (not all users have CSP, reduces compatibility)
- Transpile from Python 3.11 → rejected (over-engineering, maintenance burden)

---

## R-002: Telemetry Channel Access Strategy

**Decision**: Hybrid approach — use `ac.getCarState()` as primary API, `sim_info.py` shared memory as secondary for channels not exposed via the ac module.

**Rationale**: `ac.getCarState()` is simpler and doesn't require `_ctypes.pyd`, but some required channels (fuel, tyre wear, car damage, session type, inner/middle/outer tyre temps) are only available through shared memory.

**Primary API** (`ac.getCarState(0, acsys.CS.*)`):
- Speed, RPM, throttle, brake, steering, gear, clutch
- G-forces (3-axis), world position (3D), local velocity (3D)
- Angular velocity (yaw rate), normalized track position, lap count/time
- Tyre core temp, dynamic pressure, slip angle, slip ratio
- Suspension travel, tyre dirty level, turbo boost, ride height
- Wheel angular speed (for computing wheel speed)
- Pit lane detection: `ac.isCarInPitlane(0)`
- Car/track names: `ac.getCarName(0)`, `ac.getTrackName(0)`

**Shared memory** (`sim_info.py` → `info.physics.*`, `info.graphics.*`, `info.static.*`):
- Fuel remaining (liters): `info.physics.fuel`
- Tyre wear (4 wheels): `info.physics.tyreWear[0..3]`
- Wheel load (4 wheels): `info.physics.wheelLoad[0..3]`
- Car damage (5 zones): `info.physics.carDamage[0..4]`
- Session type: `info.graphics.session` (0=Practice, 1=Qualify, 2=Race, etc.)
- Session status: `info.graphics.status` (0=Off, 1=Replay, 2=Live, 3=Pause)
- Inner/middle/outer tyre temps: extended physics fields (if AC version supports)
- Heading/pitch/roll: `info.physics.heading`, `.pitch`, `.roll`

**Fallback behavior**: If `sim_info` fails to load (missing `_ctypes.pyd`), the app operates in reduced mode — captures all primary API channels and writes NaN for shared-memory-only channels. A warning is logged.

**Alternatives considered**:
- Pure `ac.getCarState()` only → rejected (missing fuel, wear, damage, session type)
- Pure `sim_info.py` only → rejected (adds mandatory _ctypes.pyd dependency, some channels easier via ac module)

---

## R-003: Tyre Temperature Channels

**Decision**: Capture core temperature via `ac.getCarState()` (always available) AND inner/middle/outer via extended shared memory (available in AC 1.14+). Total: 16 tyre temp channels (4 core + 12 surface zones).

**Rationale**: FR-007 requires inner, middle, and outer temperatures per tyre (12 channels). These are only available through extended shared memory fields (`tyreTempI`, `tyreTempM`, `tyreTempO` in `SPageFilePhysics`). Core temperature is a reliable fallback that's always available.

**Extended SPageFilePhysics fields** (AC 1.14+):
- `tyreTempI` (`c_float * 4`) — inner temperature per tyre
- `tyreTempM` (`c_float * 4`) — middle temperature per tyre
- `tyreTempO` (`c_float * 4`) — outer temperature per tyre

**Fallback**: If extended fields read as 0.0 for all tyres, the app writes NaN for inner/middle/outer and relies on core temp only. This is logged as a warning.

**Alternatives considered**:
- Core temp only → rejected (doesn't satisfy FR-007, loses valuable tyre analysis data)
- CSP extended API → rejected (requires Custom Shaders Patch, reduces compatibility)

---

## R-004: Active Setup File Discovery

**Decision**: At session start, scan `Documents/Assetto Corsa/setups/{car_name}/` recursively for `.ini` files. Use the most recently modified file as the "active" setup. Store its complete raw contents in the sidecar `.meta.json` along with a `setup_confidence` field indicating reliability of the discovery.

**Rationale**: AC does NOT expose the active setup filename through its Python API or shared memory. The community workaround is to check file modification timestamps, since AC touches the setup file when it's loaded for a session. **This is a best-effort heuristic, not guaranteed accurate.** The user may have edited a setup file manually (updating its timestamp) without loading it in AC, or AC may cache setups in memory without touching the file on disk.

**Search paths** (in order):
1. `Documents/Assetto Corsa/setups/{car_name}/{track_name}/*.ini` (track-specific)
2. `Documents/Assetto Corsa/setups/{car_name}/*.ini` (generic)

**Setup confidence levels** (`setup_confidence` field in `.meta.json`):
- `"high"`: Exactly one `.ini` file found in the track-specific directory, AND its modification time is within 60 seconds of session start. Very likely the active setup.
- `"medium"`: Most recently modified `.ini` found, but either multiple candidates existed or the modification time is older than 60 seconds. Probably the active setup but not certain.
- `"low"`: Setup found only in the generic (non-track-specific) directory, or modification time is older than 10 minutes. May not be the active setup.
- `null`: No setup files found at all.

**Edge cases**:
- No setup files found → proceed without setup data, log warning, confidence=null
- Multiple files with identical timestamps → pick alphabetically first, log info, confidence="medium"
- File locked/unreadable → skip, log warning
- Mod car with no setup directory → proceed without setup data, confidence=null

**Alternatives considered**:
- Require user to specify setup path → rejected (violates zero-interaction requirement SC-008)
- Store all setups in the directory → rejected (unnecessary data, most users have many setups)
- File system watcher for setup changes → rejected (over-engineering, AC's Python has no inotify)

---

## R-005: Buffered Write Strategy

**Decision**: In-memory list buffer with periodic time-based flush. Buffer limit: 1000 samples (~30-50 seconds at 20-30Hz). Flush interval: 30 seconds or when buffer reaches limit. CSV opened in append mode after initial header write. Metadata JSON written early at session start and overwritten at session end.

**Rationale**: Balances crash safety (periodic flushes) against performance (no per-sample I/O). At 30Hz with ~80 columns, each sample is ~400 bytes. 1000 samples = ~400KB in memory — negligible. A 30-second flush of 600-900 samples to CSV takes <5ms on any modern SSD/HDD.

**Flush triggers**:
1. Timer: every 30 seconds of recording
2. Buffer size: when buffer reaches 1000 samples
3. Session end: `acShutdown()` or session change detection
4. Manual: could be triggered by error conditions

**Write implementation**:
```
open file in append mode ('a')
csv.writer.writerows(buffer)
file.flush()
file.close()  (or keep open between flushes — decision: close after each flush for crash safety)
clear buffer
```

**Decision on file handle**: Close after each flush rather than keeping open. This ensures data is fully committed to disk between flushes. The overhead of open/close is negligible compared to the 30-second interval.

**Write-early metadata strategy**: The `.meta.json` sidecar is written at **session start** with all known metadata populated and `session_end` set to `null`. At session end (`acShutdown` or session transition), the file is overwritten with final values (`session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`). This ensures that even if the game crashes and `acShutdown` is never called, the metadata file exists on disk alongside the partial CSV. Downstream tools can detect a crash by checking for `session_end == null`.

**Write-early fields** (available at session start):
- `app_version`, `session_start`, `car_name`, `track_name`, `track_config`, `track_length_m`
- `session_type`, `tyre_compound`, `air_temp_c`, `road_temp_c`, `driver_name`
- `setup_filename`, `setup_contents`, `setup_confidence`
- `channels_available`, `channels_unavailable`, `sim_info_available`, `reduced_mode`
- `csv_filename`

**Deferred fields** (written at session end, `null` in early write):
- `session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`

**Alternatives considered**:
- Per-sample writes → rejected (I/O on every frame, performance impact)
- Large buffer with single write at end → rejected (total data loss on crash)
- Threading/async writes → rejected (Python 3.3 in AC, threading adds complexity and potential race conditions)
- Binary format → rejected (CSV required by spec, human-readable, tool-compatible)
- Write metadata only at session end → rejected (total metadata loss on crash, orphaned CSV with no context)

---

## R-006: Session Lifecycle Detection

**Decision**: Detect session state via shared memory `info.graphics.status` (Live/Pause/Off) and track changes in car name + track name between frames to detect session transitions.

**Rationale**: AC doesn't provide explicit "session start" or "session change" events. The app must infer session boundaries from state changes.

**Detection logic**:
- **Session start**: First `acUpdate()` where `info.graphics.status == 2` (AC_LIVE) and car is on track
- **Session end**: `acShutdown()` callback OR `info.graphics.status` changes from 2 to 0/1/3
- **Session transition**: Car name or track name changes between consecutive `acUpdate()` calls
- **Restart detection**: Lap count drops to 0 while car/track remain the same AND normalized position resets

**State machine**:
```
IDLE → RECORDING (status becomes LIVE, car on track)
RECORDING → FLUSHING (flush trigger)
FLUSHING → RECORDING (flush complete)
RECORDING → FINALIZING (session end detected)
FINALIZING → IDLE (file written and closed)
```

**Alternatives considered**:
- Only use `acShutdown()` → rejected (doesn't detect mid-session car/track changes)
- Poll file system for session changes → rejected (unreliable, slow)

---

## R-007: App UI Status Indicator

**Decision**: Minimal AC app window (200x60 pixels) with a single label element. Background color changes to indicate state: green (recording), yellow (flushing), red (error). Text shows state name.

**Rationale**: AC requires every app to have a window for registration. The spec requires a visual indicator (FR-020). A simple colored label is the most performant UI possible — no custom rendering needed.

**Implementation**:
```python
app_window = ac.newApp("AC Race Engineer")
ac.setSize(app_window, 200, 60)
status_label = ac.addLabel(app_window, "REC")
ac.setBackgroundColor(status_label, 0.0, 0.8, 0.0)  # green
ac.drawBackground(status_label, 1)
```

**Color codes**:
- Green (0.0, 0.8, 0.0): Actively recording, all channels healthy
- Yellow (0.9, 0.8, 0.0): Disk flush in progress
- Red (0.8, 0.0, 0.0): Error condition (disk full, write failure, sim_info unavailable)

**Alternatives considered**:
- Custom OpenGL rendering (circles/dots) → rejected (more complex, fragile across AC versions)
- No UI at all → rejected (AC requires app window, FR-020 requires status indicator)
- Detailed multi-label dashboard → rejected (over-engineering, "small and unobtrusive" per spec)

---

## R-008: sim_info.py and _ctypes.pyd Bundling

**Decision**: Bundle `sim_info.py` with extended physics fields. Ship without `_ctypes.pyd` binaries in the repo (licensing concerns). Document where users can find them and provide a fallback path.

**Rationale**: `_ctypes.pyd` is a compiled binary specific to the Python version and architecture. AC's Python 3.3 needs matching binaries. These are available from AC's own installation or other community apps but should not be redistributed without clear licensing.

**Fallback strategy**:
1. Try to import `sim_info` at startup
2. If it fails (missing `_ctypes.pyd`), set a flag and fall back to pure `ac` module calls
3. Log which channels are unavailable in reduced mode
4. App still records — just with fewer channels

**User instructions**: Document in README that for full channel support, users should copy `_ctypes.pyd` from `{AC_install}/apps/python/system/DLLs/` into the app's `DLLs/` folder.

**Alternatives considered**:
- Require _ctypes.pyd always → rejected (some AC installs may not have it accessible)
- Avoid sim_info entirely → rejected (loses critical channels: fuel, wear, damage, session type, tyre temp zones)
- Implement shared memory reading without ctypes → rejected (not possible in Python, ctypes IS the mechanism)

---

## R-009: Handbrake Channel

**Decision**: Include handbrake in the CSV header but expect NaN for most cars. AC does not expose a dedicated handbrake telemetry channel in its standard API.

**Rationale**: FR-005 lists handbrake as a required driver input channel. However, AC's `acsys.CS` does not include a handbrake constant, and `info.physics` does not have a handbrake field. Some modded cars may expose it through custom shared memory extensions, but standard AC does not.

**Implementation**: Attempt to read handbrake state. If unavailable (expected), write NaN. Document this limitation.

**Alternatives considered**:
- Remove handbrake from channel list → rejected (spec requires it)
- Derive from brake + speed heuristic → rejected (unreliable, not actual data)

---

## R-010: Timestamp Strategy

**Decision**: Use `time.time()` for wall-clock timestamps (Unix epoch, millisecond precision). Record both absolute timestamp and relative session time (offset from first sample).

**Rationale**: AC's `deltaT` in `acUpdate()` is the frame time delta (seconds since last call), which is useful for the throttle interval but not for absolute timing. `time.time()` provides the wall clock. `info.graphics.iCurrentTime` gives lap time in ms. Session time can be computed as `current_timestamp - session_start_timestamp`.

**Channel definitions**:
- `timestamp`: `time.time()` at sample capture (float, seconds since epoch)
- `session_time_ms`: `(current_time - session_start_time) * 1000` (float, ms since session start)
- `lap_time_ms`: from `ac.getCarState(0, acsys.CS.LapTime)` (AC's own lap timer)

**Alternatives considered**:
- Use `deltaT` accumulation → rejected (drift over time, not absolute)
- Use `time.clock()` → deprecated in 3.3, `time.time()` is more portable
- Use shared memory `iCurrentTime` for everything → rejected (that's lap time only, not session time)

---

## R-011: Reduced Mode and Graceful Degradation

**Decision**: Define an explicit "reduced mode" that activates when `sim_info.py` fails to load. Track this state in metadata via `reduced_mode` (bool) and `tyre_temp_zones_validated` (bool) fields. The app always starts recording — it never refuses to operate.

**Rationale**: The app's primary value is capturing data. Losing 28 shared-memory-only CSV channels is better than capturing nothing. Users and downstream analysis tools need to know whether a session was recorded in reduced mode so they can adjust expectations (e.g., skip tyre wear analysis if wear data is NaN).

**Reduced mode impact** (28 CSV channels + 1 metadata field affected):

| Category | Channels lost | Count |
|---|---|---|
| Fuel | fuel | 1 |
| Tyre wear | tyre_wear_fl/fr/rl/rr | 4 |
| Wheel load | wheel_load_fl/fr/rl/rr | 4 |
| Car damage | damage_front/rear/left/right/center | 5 |
| Session type | falls back to "unknown" | (metadata) |
| DRS | drs | 1 |
| ERS | ers_charge | 1 |
| Tyre temp inner | tyre_temp_inner_fl/fr/rl/rr | 4 |
| Tyre temp middle | tyre_temp_mid_fl/fr/rl/rr | 4 |
| Tyre temp outer | tyre_temp_outer_fl/fr/rl/rr | 4 |
| **Total** | | **28 CSV** + 1 metadata |

**Remaining channels in reduced mode**: 54 channels via `ac.getCarState()` and `ac.*` functions, including all timing, driver inputs, vehicle dynamics, tyre core temps, pressures, slip angles/ratios, dirty levels, wheel speeds, suspension travel, world position, turbo boost, pit lane status, and lap invalidation.

**Tyre temperature zone validation** (`tyre_temp_zones_validated` field): Even when `sim_info` loads successfully, the extended tyre temp fields (`tyreTempI`, `tyreTempM`, `tyreTempO`) may not be populated on older AC versions. At session start, the app reads all 12 zone values. If ALL 12 read as exactly `0.0`, the zones are considered unavailable — the app sets `tyre_temp_zones_validated = false` and writes NaN for inner/middle/outer temps (core temps from `ac.getCarState()` remain valid). If any zone reads non-zero, `tyre_temp_zones_validated = true`.

**Detection and logging**:
- `sim_info` import failure → log warning with exception message, set `reduced_mode = true`
- `sim_info` loads but tyre zones are zero → log info, set `tyre_temp_zones_validated = false`
- Both logged at session start and recorded in `.meta.json`

**Alternatives considered**:
- Refuse to record without sim_info → rejected (violates zero-interaction principle SC-008, loses all data for users who can't provide _ctypes.pyd)
- Silently record NaN without metadata flags → rejected (downstream tools can't distinguish "channel unavailable" from "car doesn't have this feature")
- Attempt multiple sim_info load retries → rejected (if _ctypes.pyd is missing, retries won't help; adds startup latency)
