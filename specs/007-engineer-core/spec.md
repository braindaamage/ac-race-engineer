# Feature Specification: Engineer Core (Deterministic Layer)

**Feature Branch**: `007-engineer-core`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Phase 5.2 Engineer Core — deterministic session summarizer, setup parameter reader, change validator, and setup writer"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session Summary for AI Consumption (Priority: P1)

The AI engineer agent needs to receive a compact, structured summary of a driving session to reason about what setup changes to recommend. Today, the full analyzed session contains thousands of data points across laps, corners, stints, and metrics — far too much for efficient LLM consumption. The system must distill this into a token-efficient summary that preserves all the information the engineer needs to make recommendations, while discarding raw detail.

**Why this priority**: Without a compact summary, the AI agent cannot efficiently process session data. This is the single most critical input to the engineer — everything else (parameter reading, validation, writing) depends on the agent first understanding what happened in the session.

**Independent Test**: Can be fully tested by passing an AnalyzedSession object and verifying the returned summary contains the correct car, track, lap count, best lap identification, detected problems, stint breakdowns, and setup info — all without any LLM or file system access.

**Acceptance Scenarios**:

1. **Given** a completed analyzed session with 15 laps (3 outlaps, 10 flying, 2 inlaps) across 2 stints, **When** the summarizer processes it, **Then** the summary includes only the 10 flying laps with their times, identifies the best lap, shows delta-to-best for each other flying lap, and breaks down metrics per stint.
2. **Given** an analyzed session where signals detected high understeer and tyre temperature spread, **When** the summarizer processes it, **Then** the summary lists "high_understeer" and "tyre_temp_spread_high" as detected problems.
3. **Given** an analyzed session with corner-level metrics showing 3 corners with understeer ratios above 1.3, **When** the summarizer processes it, **Then** the summary includes the top corner-specific issues ranked by severity.
4. **Given** the same analyzed session processed twice, **When** comparing both summaries, **Then** they are identical (deterministic output).
5. **Given** an analyzed session with zero flying laps (all outlaps/inlaps), **When** the summarizer processes it, **Then** it returns a valid summary with an empty flying laps list and no stint breakdowns, without errors.
6. **Given** an analyzed session where tyre temperature data is unavailable, **When** the summarizer processes it, **Then** the summary omits tyre-related averages gracefully instead of failing.

---

### User Story 2 - Setup Parameter Range Discovery (Priority: P2)

Before the AI engineer can propose setup changes, it needs to know what parameters a car supports and what values are valid. Assetto Corsa stores parameter definitions (min, max, step) in car data files within the game installation directory. The system must read these definitions so the engineer knows the boundaries of what it can adjust, and so proposed values can be validated before any file is written.

**Why this priority**: The engineer cannot safely propose changes without knowing valid ranges. This is the safety gate that prevents writing nonsensical values to setup files. It must work for any car — vanilla or modded — and must degrade gracefully when AC is not installed or car data is incomplete.

**Independent Test**: Can be fully tested by pointing the reader at a directory containing car data files (real or fixture) and verifying it returns correct parameter ranges. Can also test the "AC not installed" path by pointing at a nonexistent directory.

**Acceptance Scenarios**:

1. **Given** a valid AC install path and a car name with complete data files, **When** the reader loads parameter ranges, **Then** it returns a structured result mapping each section+parameter to its min, max, and step values.
2. **Given** a car name and an AC install path that does not exist, **When** the reader attempts to load ranges, **Then** it returns an empty result (no parameters found) without raising an error.
3. **Given** a car whose data files are partially malformed (some parameters missing range definitions), **When** the reader loads ranges, **Then** it returns ranges for the valid parameters and skips the malformed ones.
4. **Given** loaded parameter ranges, **When** looking up the range for a specific section and parameter name (e.g., section "FRONT", parameter "CAMBER"), **Then** the system returns the min/max/step or None if that parameter has no range data.
5. **Given** a modded car with non-standard parameter names, **When** the reader loads ranges, **Then** it discovers and returns ranges for all parameters defined in the data files without assuming any hardcoded parameter names.

---

### User Story 3 - Setup Change Validation (Priority: P3)

When the AI engineer proposes a list of setup changes (e.g., "increase front camber by 0.5 degrees"), each change must be validated against the car's known parameter ranges before anything is written to disk. The validator checks each proposed value and reports whether it's valid, out of range (providing the clamped value), or has no range data available (warning but allowing the change to proceed).

**Why this priority**: This is the safety layer between the AI's recommendations and actual file modifications. Without it, the AI could propose values outside the car's physical limits, resulting in broken or nonsensical setups.

**Independent Test**: Can be fully tested by providing a set of parameter ranges and a list of proposed changes, then verifying each change gets the correct validation status — no file system access needed.

**Acceptance Scenarios**:

1. **Given** a car with front camber range [-5.0, 0.0] step 0.1, **When** the engineer proposes front camber = -2.5, **Then** the validator marks it as valid with the proposed value accepted.
2. **Given** a car with front camber range [-5.0, 0.0] step 0.1, **When** the engineer proposes front camber = -7.0, **Then** the validator marks it as out-of-range and provides the clamped value of -5.0.
3. **Given** a car with front camber range [-5.0, 0.0] step 0.1, **When** the engineer proposes front camber = 1.0, **Then** the validator marks it as out-of-range and provides the clamped value of 0.0.
4. **Given** a parameter with no known range data, **When** the engineer proposes a value for it, **Then** the validator marks it as "no range data" with a warning, but includes the proposed value as-is (allowing the change to proceed).
5. **Given** a list of 5 proposed changes where 3 are valid, 1 is out-of-range, and 1 has no range data, **When** validated, **Then** the result contains 5 individual validation outcomes — one per change — with correct statuses.

---

### User Story 4 - Safe Setup File Writing (Priority: P4)

After changes are validated and accepted, the system must apply them to the actual setup .ini file. This must be done safely: create a backup first, write atomically (no partial writes), preserve all parameters not included in the changes, and refuse to write if the change list is empty.

**Why this priority**: This is the final step that makes recommendations real. It is lower priority than validation because a broken writer could corrupt setup files — safety must be proven before writes happen.

**Independent Test**: Can be fully tested by creating a temporary setup .ini file, applying changes, and verifying the file was modified correctly, a backup was created, and unchanged parameters are preserved.

**Acceptance Scenarios**:

1. **Given** a setup file with 20 parameters across 5 sections, **When** applying 2 validated changes, **Then** the 2 changed parameters have their new values, the other 18 parameters are identical to the original, and a backup file exists with the original content.
2. **Given** a setup file, **When** applying changes and the write fails mid-operation, **Then** the original file remains intact (no partial writes).
3. **Given** an empty list of changes, **When** attempting to write, **Then** the system refuses and reports an error without touching the file.
4. **Given** a setup file, **When** changes are applied successfully, **Then** a backup of the original file is created in a predictable location before any modification occurs.
5. **Given** a setup file with comments and formatting, **When** changes are applied, **Then** the file structure and non-changed content are preserved as closely as possible.

---

### Edge Cases

- What happens when an analyzed session has exactly one flying lap? The summarizer must handle single-lap sessions (no delta-to-best needed, single-stint only).
- What happens when all laps in a session are classified as invalid? The summarizer returns a valid summary with zero flying laps and appropriate empty fields.
- What happens when the AC install path is configured but the specific car's data directory does not exist? The parameter reader returns an empty result.
- What happens when a setup .ini file is read-only or locked by another process? The writer must report the error clearly rather than silently failing.
- What happens when two validated changes target the same section and parameter? The last change in the list takes precedence.
- What happens when a setup file has sections or parameters not present in any parameter range data? They are preserved as-is during writing.
- What happens when the backup location already has a file from a previous backup? The system must not silently overwrite previous backups without a clear policy (e.g., timestamped backups or rotating backups).
- What happens when a stint has no setup associated? The summarizer reports the stint without setup information rather than failing.

## Requirements *(mandatory)*

### Functional Requirements

**Session Summarizer**

- **FR-001**: System MUST produce a session summary from an AnalyzedSession containing: car name, track name, session date, total lap count, and total flying lap count.
- **FR-002**: System MUST include only flying laps (classification = "flying") in the summary's lap list, excluding outlaps, inlaps, invalid, and incomplete laps.
- **FR-003**: System MUST identify the best flying lap (lowest lap time) and include the delta-to-best for every other flying lap.
- **FR-004**: System MUST include detected problem signals (from the knowledge base signal detection) in the summary.
- **FR-005**: System MUST include the top corner-specific issues, prioritized by severity, with a configurable maximum count (default: 5).
- **FR-006**: System MUST include per-stint breakdowns with: lap number range, flying lap count, mean lap time, lap time trend (improving/degrading/stable), and tyre temperature trend.
- **FR-007**: System MUST include the active setup information (filename and parameters) for each stint when available.
- **FR-008**: System MUST include session-wide averages for tyre temperatures, tyre pressures, and slip angles across all flying laps when data is available.
- **FR-009**: System MUST produce identical output for identical input (deterministic — no randomness, no timestamps in output).
- **FR-010**: System MUST NOT modify the input AnalyzedSession object.
- **FR-011**: System MUST handle sessions with zero flying laps by returning a valid summary with empty lap/stint sections.
- **FR-012**: System MUST omit metric fields gracefully when the underlying data is unavailable (e.g., no tyre data) rather than failing.

**Setup Parameter Reader**

- **FR-013**: System MUST read parameter range definitions (min, max, step) from the car's data files within the AC installation directory.
- **FR-014**: System MUST return an empty result (not an error) when the AC install path does not exist or is not configured.
- **FR-015**: System MUST return a partial result when car data files are incomplete or malformed, extracting whatever valid ranges are available.
- **FR-016**: System MUST support looking up the valid range for a specific section + parameter combination and return None when no range data exists for that combination.
- **FR-017**: System MUST work generically for any car (vanilla or modded) without hardcoding parameter names or car-specific logic.

**Setup Change Validator**

- **FR-018**: System MUST validate each proposed setup change against the car's known parameter ranges and return a per-change validation result.
- **FR-019**: System MUST report "valid" when a proposed value is within the parameter's [min, max] range.
- **FR-020**: System MUST report "out of range" with the clamped value (snapped to nearest boundary) when a proposed value exceeds the range.
- **FR-021**: System MUST report "no range data" as a warning (not an error) when a parameter has no known range, passing the proposed value through unchanged.
- **FR-022**: System MUST perform all validation without touching any files on disk.

**Setup File Writer**

- **FR-023**: System MUST create a backup of the original setup file before making any modifications.
- **FR-024**: System MUST write changes atomically — either all changes succeed or the original file remains untouched.
- **FR-025**: System MUST preserve all parameters, sections, and structure in the setup file that are not targeted by the change list.
- **FR-026**: System MUST refuse to write when given an empty change list and report this as an error.
- **FR-027**: System MUST only accept changes that have been through the validation step — the writer receives validated change objects, not raw proposals.

### Key Entities

- **SessionSummary**: A compact representation of an analyzed driving session, containing header info (car, track, date), flying lap list with times and deltas, detected problems, corner issues, stint breakdowns, setup info, and session-wide metric averages.
- **FlyingLapSummary**: Per-lap entry within the session summary, containing lap number, lap time, delta to best, and key metrics (e.g., tyre temps, grip level).
- **StintSummary**: Per-stint breakdown within the session summary, containing lap range, flying lap count, mean lap time, lap time trend direction, tyre temperature trend, and active setup reference.
- **CornerIssueSummary**: A prioritized corner-specific problem entry, containing corner number, issue type, severity, and metric value.
- **ParameterRange**: The valid range for a single setup parameter, containing section name, parameter name, minimum value, maximum value, and step size.
- **ParameterRangeSet**: A collection of all parameter ranges for a specific car, with lookup capability by section + parameter name.
- **ProposedChange**: A single proposed setup modification, containing section name, parameter name, and new value.
- **ValidationResult**: The outcome of validating a single proposed change, containing the original proposal, validation status (valid / out-of-range / no-range-data), accepted value (original or clamped), and optional warning message.
- **ChangeOutcome**: The result of applying a single validated change to a setup file, containing section, parameter, old value, new value.
- **SetupChange**: A fully described setup modification proposed by the AI engineer, containing section name, parameter name, value before (optional), value after, reasoning (why this change helps), expected effect (what the driver will feel), and confidence level (high / medium / low).
- **DriverFeedback**: A driving technique observation from the engineer, containing area (e.g., braking, throttle application), what was observed, what to try next, which corners are affected, and severity (high / medium / low).
- **EngineerResponse**: The complete output of the AI engineer for a session, containing the list of setup changes proposed, driver feedback items, a short summary for display, a full explanation in plain language, and an overall confidence level.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given any valid AnalyzedSession, the summarizer produces a complete summary in under 100 milliseconds without errors.
- **SC-002**: The session summary for a typical 20-lap session uses fewer than 2,000 tokens when serialized as text, making it practical for LLM consumption within context limits.
- **SC-003**: 100% of setup parameter ranges present in a car's data files are correctly discovered and returned by the parameter reader.
- **SC-004**: The parameter reader returns an empty result (zero errors, zero crashes) for 100% of missing/invalid AC install paths tested.
- **SC-005**: 100% of proposed changes with known ranges are correctly validated (in-range accepted, out-of-range clamped to boundary).
- **SC-006**: The setup writer preserves 100% of unchanged parameters after applying changes — no data loss or corruption.
- **SC-007**: A backup file exists for every setup file modified, containing the exact original content.
- **SC-008**: All four components (summarizer, parameter reader, validator, writer) are fully testable with unit tests that require no running game, no LLM, and no external services.
- **SC-009**: The summarizer produces bit-identical output when run twice on the same input session.

### Assumptions

- The AC installation directory structure follows the standard Assetto Corsa layout: `<install_path>/content/cars/<car_name>/data/` for car data files.
- Setup .ini files use the standard INI format already handled by the existing parser (sections with key=value pairs).
- Car data files defining parameter ranges are INI-formatted or similarly structured text files within the car's data directory.
- The backup strategy for setup files uses timestamped copies (e.g., `setup_name.ini.bak.20260304_153000`) to avoid overwriting previous backups.
- The maximum number of corner issues included in the summary defaults to 5 but is configurable.
- "Severity" for corner issues is derived from how far a metric deviates from ideal values (e.g., understeer ratio distance from 1.0).
