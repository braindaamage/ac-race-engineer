# Feature Specification: Telemetry Parser

**Feature Branch**: `003-telemetry-parser`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "Build a telemetry parser module that transforms raw telemetry session files (CSV data + JSON metadata produced by the in-game capture app) into structured, per-lap and per-corner segments ready for analysis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lap Segmentation and Classification (Priority: P1)

The Analyzer module receives a session's CSV file and metadata JSON. It needs each lap as a discrete, self-contained data segment with all telemetry channels and a classification label ("flying", "outlap", "inlap", or "invalid") so it can compute per-lap metrics and skip unusable laps.

**Why this priority**: All downstream analysis depends on correctly identified and classified laps. Without this, no metrics, setup correlations, or display data can be produced. This is the foundational capability — every other story builds on it.

**Independent Test**: Parse a known session CSV with multiple laps (including pit entry and exit) and verify that each lap segment's boundaries match the expected lap count transitions and that each classification matches observed pit-lane-status patterns.

**Acceptance Scenarios**:

1. **Given** a session CSV with 10 recorded laps including 1 outlap, 8 flying laps, and 1 inlap, **When** the parser processes the session, **Then** it produces exactly 10 lap segments each classified correctly, with no samples lost between consecutive laps.
2. **Given** a session where the driver never left the pit lane, **When** the parser processes the session, **Then** it produces zero flying-lap segments and returns a valid (non-error) result.
3. **Given** a session with zero completed laps (driver quit immediately), **When** the parser processes the session, **Then** it produces output without errors, noting that no lap count transitions were detected.
4. **Given** a session where every lap is flagged invalid by AC, **When** the parser processes the session, **Then** it produces all laps in the output each classified `invalid`, with no laps silently dropped.

---

### User Story 2 - Setup-Stint Association and Setup Parsing (Priority: P2)

The AI Engineer module needs to know which setup was active during each lap, and what that setup's parameters were. Given multiple setup changes during a session (stored in the metadata), each lap must reference the exact setup that was loaded when that lap was driven, and every parameter from that setup must be available in structured form.

**Why this priority**: Setup-behavior correlation is the AI Engineer's core capability. Incorrect setup association or missing parameters would produce wrong engineering recommendations.

**Independent Test**: Parse a session with 3 setup changes (at laps 1, 6, and 12) and verify that laps 1–5 reference setup A, laps 6–11 reference setup B, and laps 12+ reference setup C. Verify that all .ini parameters from a modded car are present in the structured output.

**Acceptance Scenarios**:

1. **Given** a metadata file with `setup_history` entries at laps 1, 6, and 12, **When** the parser associates setups with laps, **Then** lap 5 references the entry at lap 1, lap 7 references the entry at lap 6, and lap 15 references the entry at lap 12.
2. **Given** a legacy v1.0 metadata file with flat `setup_filename`, `setup_contents`, and `setup_confidence` fields instead of a `setup_history` array, **When** the parser reads it, **Then** it converts those fields to a single-entry `setup_history` equivalent (active from lap 1) and produces structurally identical output.
3. **Given** a parsed setup .ini from a modded car with 40 non-vanilla parameters, **When** the parser extracts its parameters, **Then** all 40 parameters are present in the structured output, each with its section name, parameter name, and value.

---

### User Story 3 - Corner Detection Across Laps (Priority: P2)

The Analyzer needs consistent corner segments across all laps of a session. Corner 3 in lap 1 must refer to the same physical location as corner 3 in lap 5, regardless of minor differences in the driver's line. Detection must work for any track without a hardcoded corner map.

**Why this priority**: Without consistent corner numbering, the Analyzer cannot produce meaningful per-corner statistics (e.g., "average entry speed at corner 3 across 8 laps"). Inconsistent detection silently produces incorrect results.

**Independent Test**: Parse a multi-lap session and verify that each lap has the same corner count, and that each corner's apex normalized position falls within ±5% of the session-wide reference position for that corner.

**Acceptance Scenarios**:

1. **Given** a 5-lap session on a 10-corner circuit, **When** the parser detects corners, **Then** each lap contains exactly 10 corner segments, and corner N in any lap has its apex within ±5% normalized track position of corner N's apex in all other laps.
2. **Given** a session on a track with a chicane (two rapid direction changes in quick succession), **When** the parser detects corners, **Then** the two direction changes are identified as two separate corners, not merged into one.
3. **Given** a session on an oval with only 2 corners and a very long straight, **When** the parser detects corners, **Then** it identifies exactly 2 corners and does not produce phantom corners on the straights.

---

### User Story 4 - Data Quality Flagging (Priority: P3)

The Desktop App and Analyzer need to know whether a lap's telemetry data is reliable. Laps with data gaps, teleportation artifacts, or mid-lap pauses must be flagged with specific named quality warnings — but never silently dropped. The user must be able to see all laps, understand quality issues, and decide whether to include or exclude them.

**Why this priority**: Silently including bad data corrupts analysis; silently dropping laps hides information. Transparent quality flagging is essential for trust in the parser's output.

**Independent Test**: Provide a session CSV with intentionally introduced gaps, position jumps, and zero-speed periods, then verify that each anomalous lap appears in the output with the expected named quality warning.

**Acceptance Scenarios**:

1. **Given** a session where lap 4 contains a 2-second gap in the telemetry time series, **When** the parser processes it, **Then** lap 4 is present in the output with a `time_series_gap` quality warning indicating the approximate position of the gap.
2. **Given** a session where lap 7 shows a normalized-position jump of 0.3 in a single sample, **When** the parser processes it, **Then** lap 7 is present in the output with a `position_jump` quality warning.
3. **Given** a session interrupted by a game crash (session_end is null in metadata), **When** the parser processes it, **Then** it uses the actual CSV data to determine available laps, marks the last partial lap `incomplete`, and returns without error.

---

### User Story 5 - Cached Session Access (Priority: P3)

Downstream tools need to access parsed session data multiple times without re-reading and re-processing the raw CSV each time. A parsed session must be storable to a file and reloadable, producing data structurally identical to the original parse result.

**Why this priority**: Raw CSV files can be large (thousands of samples per lap, 82 channels). Re-parsing on every access creates unnecessary delay and redundant processing, which degrades the Desktop App's responsiveness.

**Independent Test**: Parse a session once, save the intermediate output, reload it, and verify that the reloaded data is structurally identical to the original parsed output for all fields.

**Acceptance Scenarios**:

1. **Given** a parsed session, **When** the session is saved to the intermediate format and reloaded, **Then** all lap segments, corner segments, setup associations, quality flags, and metadata fields are preserved exactly.
2. **Given** an intermediate-format file saved by the parser, **When** any downstream tool loads it, **Then** it receives the same data structures as if it had called the parser directly on the raw CSV.

---

### Edge Cases

- What happens when a session CSV has zero rows? → Parser returns a valid empty session result with no error.
- What happens when a telemetry channel contains only NaN values (reduced capture mode)? → That channel is marked unavailable per lap; all other channels are still processed normally.
- What happens when the last lap is cut short by session end? → The partial lap is included as a segment classified `incomplete`, not silently dropped.
- What happens when two consecutive samples share the same timestamp (duplicate)? → Duplicates are detected and noted as a quality warning on the affected lap.
- What happens when a setup .ini entry contains a non-numeric value? → The value is stored as a string type and excluded from numeric-range analysis.
- What happens when the car enters pit lane mid-lap? → The transition is used to classify the lap as `inlap`; telemetry within the pit lane is part of that lap's segment.
- What happens when a session lasts under 1 minute and the driver barely moved? → The parser produces whatever lap segments can be detected from the available data, even if that is just one incomplete segment.

## Requirements *(mandatory)*

### Functional Requirements

#### Lap Segmentation

- **FR-001**: The parser MUST segment the continuous telemetry stream into individual laps using transitions in the lap count channel, producing one lap segment per detected lap count increment.
- **FR-002**: Each lap segment MUST contain the complete time series for all telemetry channels present in the source CSV, with no samples from that lap omitted.
- **FR-003**: The parser MUST include partial laps at the start and end of the session (where no complete lap count cycle occurred) as separate segments classified `incomplete`.
- **FR-004**: The parser MUST NOT lose any samples between consecutive laps: the last sample of lap N and the first sample of lap N+1 MUST be temporally contiguous.

#### Lap Classification

- **FR-005**: The parser MUST classify each lap segment as exactly one of: `flying`, `outlap`, `inlap`, `invalid`, or `incomplete`.
- **FR-006**: A lap MUST be classified `outlap` when its first sample has the car in the pit lane and subsequent samples show the car transitioning to the track.
- **FR-007**: A lap MUST be classified `inlap` when the car transitions from track to pit lane before the next lap count increment.
- **FR-008**: A lap MUST be classified `invalid` when AC's lap-invalid flag is set for any sample in that lap, or when quality validation detects a disqualifying anomaly (e.g., position teleportation exceeding the jump threshold).
- **FR-009**: A lap MUST be classified `flying` when none of the `outlap`, `inlap`, `invalid`, or `incomplete` conditions apply.

#### Corner Detection

- **FR-010**: The parser MUST identify corners within each lap using lateral G-force magnitude, steering input magnitude, and speed reduction patterns, without relying on any hardcoded track map, corner count, or car/track-specific configuration.
- **FR-011**: Each detected corner MUST include an entry point, apex point, and exit point expressed as normalized track positions (0.0–1.0).
- **FR-012**: Corner detection MUST calibrate its sensitivity thresholds from the session's own telemetry distribution, adapting to different cars and tracks without manual tuning.
- **FR-013**: Corner numbering MUST be consistent across all laps of the same session: corner N in lap X and corner N in lap Y MUST refer to the same physical location on track, with apex positions within ±5% normalized track position of each other.
- **FR-014**: The parser MUST NOT produce phantom corners during sustained straight-line sections where lateral G-force and steering inputs remain below the detection threshold.
- **FR-015**: The parser MUST detect rapid successive direction changes (chicanes) as distinct individual corners, not as a single merged event.

#### Setup-Stint Association

- **FR-016**: The parser MUST associate each lap with the most recent `setup_history` entry whose `lap` value is less than or equal to the lap's number.
- **FR-017**: The parser MUST support v2.0 metadata with a `setup_history` array containing one or more entries.
- **FR-018**: The parser MUST support v1.0 legacy metadata with flat `setup_filename`, `setup_contents`, and `setup_confidence` fields by treating them as a single-entry `setup_history` array active from lap 1.

#### Setup File Parsing

- **FR-019**: The parser MUST parse the raw .ini text from each `setup_history` entry into a structured collection of parameters, each identified by section name, parameter name, and value.
- **FR-020**: The parser MUST extract all parameters present in the .ini text regardless of their names, supporting arbitrary modded car parameters without any hardcoded parameter list.
- **FR-021**: Parameters with numeric values MUST be stored as numbers; parameters with non-numeric values MUST be stored as strings.

#### Data Quality Validation

- **FR-022**: The parser MUST detect and attach named quality warnings to laps for the following conditions:
  - `time_series_gap`: consecutive samples separated by more than 0.5 seconds
  - `position_jump`: normalized position change greater than 0.05 in a single sample
  - `zero_speed_mid_lap`: speed at or near zero for more than 3 seconds when normalized position is between 10% and 90% of the lap
  - `incomplete`: lap segment has no closing lap count transition (session ended mid-lap)
  - `duplicate_timestamp`: consecutive samples share the same timestamp
- **FR-023**: Laps with quality warnings MUST be included in the parser output with their warnings attached; they MUST NOT be silently dropped.
- **FR-024**: Each quality warning MUST include: warning type, approximate normalized position where detected, and a human-readable description.

#### Intermediate Format and File Safety

- **FR-025**: The parser MUST provide a save operation that serializes the full parsed session to a file, and a load operation that restores it, producing data structurally identical to the original parsed output.
- **FR-026**: The parser MUST NOT modify the source CSV or metadata JSON files under any circumstance.

#### Robustness

- **FR-027**: The parser MUST handle sessions with zero lap count transitions (driver never completed a lap) by returning a valid session result with zero lap segments and no error.
- **FR-028**: The parser MUST handle telemetry channels containing only NaN values by marking those channels as unavailable per lap rather than raising an error.
- **FR-029**: When `session_end`, `laps_completed`, or `total_samples` are null in the metadata (game crash), the parser MUST derive those values from the actual CSV data.
- **FR-030**: The parser MUST handle sessions with only invalid laps by including all laps in the output each classified `invalid`, with no laps omitted.

### Key Entities

- **ParsedSession**: Top-level container. Holds session-level metadata (car, track, track config, track length, session type, tyre compound, driver name, temperatures), the ordered list of LapSegments, and the list of SetupEntries derived from `setup_history`.
- **LapSegment**: One lap's worth of telemetry. Contains: lap number, classification (`flying`/`outlap`/`inlap`/`invalid`/`incomplete`), start and end timestamps, start and end normalized positions, time series data for all channels, the list of CornerSegments detected within the lap, the active SetupEntry reference, and the list of QualityWarnings.
- **CornerSegment**: One detected corner. Contains: session-consistent corner number, entry/apex/exit normalized positions, minimum speed at apex, maximum lateral G-force, and entry/exit speeds.
- **SetupEntry**: One parsed setup stint. Contains: the lap number when it became active, trigger event, confidence level, and the list of SetupParameters.
- **SetupParameter**: One parameter from a setup .ini file. Contains: section name, parameter name, and value (numeric or string).
- **QualityWarning**: A data quality issue on a lap. Contains: warning type, normalized position where detected, and a human-readable description.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A session file with 20 laps is fully parsed into lap segments in under 5 seconds on typical developer hardware, excluding initial file read time.
- **SC-002**: Corner detection produces consistent corner numbering across all laps, with apex positions varying by no more than ±5% normalized track position for the same corner across laps, validated on a test set covering at least 5 distinct tracks (including at least one oval and one track with a chicane).
- **SC-003**: Lap type classification achieves 100% accuracy on a manually labeled test set of at least 50 laps drawn from at least 3 different sessions (including sessions with pit stops, invalid laps, and partial laps).
- **SC-004**: All 5 named data quality warning conditions are correctly detected and attached to affected laps in a test set with intentionally introduced anomalies covering each condition.
- **SC-005**: Setup-stint association is correct for 100% of laps in sessions with 1, 2, and 3 setup changes, verified against manually annotated sessions.
- **SC-006**: A session interrupted by a game crash (null `session_end`) is parsed without raising an error and produces all recoverable lap segments, with the last partial lap classified `incomplete`.
- **SC-007**: Sessions from at least 3 modded cars with non-vanilla setup parameters are parsed without errors, with all .ini parameters present and correctly typed in the structured output.
- **SC-008**: Reloading a saved intermediate-format session produces data structurally identical to the originally parsed session for all fields, validated across at least 10 diverse test sessions.

## Assumptions

- Telemetry CSV files use the schema produced by the Phase 1/1.5 in-game capture app (82 channels at ~22–25 Hz). No compatibility with earlier capture formats is required.
- The `lap_count` and `normalized_position` channels are always present and non-NaN in valid captures; they are the authoritative source for lap segmentation.
- Corner detection calibrates thresholds from each session's own telemetry distribution (percentile-based), making it self-adapting rather than relying on absolute fixed values.
- The .ini setup format follows standard INI conventions: sections in `[brackets]`, key-value pairs with `=`, comments prefixed with `;`. Non-standard INI dialects are out of scope.
- A time series gap threshold of 0.5 seconds is appropriate for ~22–25 Hz capture (expected inter-sample interval ~40–45 ms); gaps beyond this indicate dropped samples rather than normal sampling variance.
- Intermediate caching is session-scoped (one parsed session → one cache file). Partial or incremental caching is not required.
- The parser processes completed session files only; real-time streaming operation is out of scope.
- Sessions from mods may have unusual numeric ranges for some telemetry channels, but the parser does not validate physical plausibility of channel values — that is the Analyzer's responsibility.
