# Feature Specification: Setup Stint Tracking

**Feature Branch**: `002-setup-stint-tracking`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "Improve setup file tracking in the telemetry capture app to provide accurate per-stint setup context for AI analysis in later phases."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track-Specific Setup Is Recognized as Reliable (Priority: P1)

As a driver who saves setups in the track-specific folder, I want the race engineer to correctly identify that setup as highly reliable so that the AI analysis in later phases is based on accurate setup context rather than being told the data is questionable.

**Why this priority**: Inaccurate confidence scoring directly degrades AI recommendation quality. If a correctly identified setup is marked "low" confidence, the engineer may ignore or caveat valid correlations. This is a data quality regression that affects all downstream phases.

**Independent Test**: Can be fully tested by running a session with a single `.ini` file present in the track-specific setups folder (regardless of how old the file is) and verifying that the resulting `.meta.json` records `confidence = "high"` in the initial setup history entry.

**Acceptance Scenarios**:

1. **Given** exactly one `.ini` file exists in the track-specific folder (`setups/{car}/{track}/`), **When** a session ends and the metadata is written, **Then** the setup history entry has `confidence = "high"`, regardless of the file's modification timestamp.
2. **Given** multiple `.ini` files exist in the track-specific folder, **When** a session ends and the metadata is written, **Then** `confidence = "medium"` (multiple candidates — most recent selected as tiebreaker), never "low".
3. **Given** no `.ini` files exist in the track-specific folder but one exists in the generic car folder, **When** a session ends and the metadata is written, **Then** `confidence = "low"` (fallback to generic folder).
4. **Given** a single `.ini` file in the track-specific folder was last modified 48 hours ago, **When** a session ends, **Then** `confidence` is still "high" — file age does not demote a track-specific solo file.

---

### User Story 2 - Setup Change After a Pit Stop Is Captured (Priority: P1)

As a driver who adjusts my setup during a pit stop, I want each stint to be associated with the exact setup that was active for that stint, so that the AI race engineer can correlate my driving behavior changes with the setup changes I made.

**Why this priority**: Without per-stint setup tracking, the AI has no way to attribute behavior differences across stints to setup changes versus driver adaptation. This is a prerequisite for meaningful setup recommendations in Phase 5.

**Independent Test**: Can be fully tested in a single session by pitting, saving a modified setup, and re-joining; then verifying the `.meta.json` contains a second setup entry in the history timeline showing the changed setup and the lap at which it was applied.

**Acceptance Scenarios**:

1. **Given** a driver pits and returns to the track without changing the setup, **When** the metadata is written, **Then** the setup history contains only one entry (no duplicates).
2. **Given** a driver pits, saves a modified setup, and returns to the track, **When** the metadata is written, **Then** the setup history contains two entries: the original setup from session start and the changed setup with the lap number at which pit exit occurred.
3. **Given** a driver pits three times, changing the setup each time, **When** the metadata is written, **Then** the setup history contains four entries (initial + three changes), each with the correct lap count and trigger event.
4. **Given** a driver pits and changes the setup, but the new file cannot be read (e.g., locked or missing), **When** the metadata is written, **Then** a setup history entry is still recorded for the pit exit event, with `filename` and `contents` set to null — the session is not lost.

---

### User Story 3 - Setup History Is Queryable by Stint (Priority: P2)

As a Phase 2 parser or Phase 5 AI engine, I want to look up which setup was active on any given lap, so that I can associate telemetry segments with their setup context without guessing.

**Why this priority**: Without a well-structured timeline, the parser would need heuristics to reconstruct per-stint setup context. A clear, ordered history eliminates that ambiguity.

**Independent Test**: Can be tested by writing a small script that reads a `.meta.json` produced by a multi-stint session and, given any lap number, returns the setup that was active at that lap — without examining the CSV file.

**Acceptance Scenarios**:

1. **Given** a `.meta.json` with a three-entry setup history (session start at lap 0, pit exit at lap 8, pit exit at lap 15), **When** a consumer queries "what setup was active at lap 10?", **Then** the answer is the second entry (applied at lap 8).
2. **Given** a `.meta.json` with a single setup entry (no pit stops), **When** a consumer reads the setup history, **Then** there is exactly one entry with `trigger = "session_start"`.
3. **Given** a session where no setup file was found at session start and no changes were detected during pit exits, **When** the metadata is written, **Then** the setup history contains one entry with `trigger = "session_start"` and `filename`, `contents`, `confidence` all null.

---

### Edge Cases

- What happens when the driver pits repeatedly in a very short window (e.g., drive-through penalty, immediate re-pit)? Each pit exit triggers a setup re-read and comparison independently; only genuine content changes produce new history entries.
- What happens if the setup directory is temporarily inaccessible during a pit exit? The entry is recorded with nulls for file data; the previous valid setup entry remains intact.
- What happens if two consecutive pit exits produce identically named but differently-contented setup files? Content comparison (not just filename) determines whether an entry is added — a content change always produces a new entry.
- What happens if the setup changes mid-lap before the car ever pits (e.g., file replaced externally)? This is out of scope — only pit exits serve as capture triggers.
- What happens in a crash scenario where the session ends without a final metadata write? The early-write metadata (written at session start) contains at least the initial setup history entry. Subsequent entries written after pit exits are persisted to disk as part of the periodic metadata refresh strategy defined in this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST assign `confidence = "high"` when exactly one `.ini` file is found in the track-specific setups directory (`setups/{car}/{track}/`), regardless of the file's modification timestamp.
- **FR-002**: The system MUST assign `confidence = "medium"` when multiple `.ini` files are found in the track-specific setups directory; the most recently modified file MUST be selected as the active setup when multiple candidates exist in the same directory.
- **FR-003**: The system MUST assign `confidence = "low"` when no `.ini` files are found in the track-specific directory and the setup is sourced from the generic car directory instead.
- **FR-004**: Modification timestamps MUST only be used as a tiebreaker when multiple files are present within the same directory level; timestamps MUST NOT influence confidence when comparing files from different directory levels (track-specific vs. generic).
- **FR-005**: The system MUST detect pit lane exit events during a recording session. On each pit exit, the system MUST re-read the setup file for the current car and track using the same discovery logic as at session start.
- **FR-006**: After a pit exit setup read, the system MUST compare the newly read setup contents against the most recently recorded setup contents. A new history entry MUST be added only if the contents differ (string equality comparison on full file text).
- **FR-007**: The system MUST maintain a `setup_history` field in the session metadata containing an ordered list of setup capture events. Each entry MUST include: `timestamp` (ISO 8601 string), `trigger` ("session_start" or "pit_exit"), `lap` (integer lap count at capture time), `filename` (string or null), `contents` (complete raw `.ini` text, string or null), and `confidence` ("high", "medium", "low", or null).
- **FR-008**: The `setup_history` list MUST always contain at least one entry, corresponding to the setup read at session start. If no setup file was found, the entry MUST still be present with null values for `filename`, `contents`, and `confidence`.
- **FR-009**: The flat top-level fields `setup_filename`, `setup_contents`, and `setup_confidence` MUST be removed from the metadata schema and replaced by `setup_history`. These fields MUST NOT appear in any metadata file produced by the updated app.
- **FR-010**: The setup history MUST be included in the early metadata write at session start. When a new entry is appended after a pit exit, the on-disk metadata file MUST be updated to reflect the new entry within the same frame cycle that the change is detected.
- **FR-011**: The system MUST NOT add a new setup history entry when the driver exits the pit lane and the setup contents are byte-for-byte identical to the previous entry.
- **FR-012**: If the setup file cannot be read during a pit exit (file locked, missing, or unreadable), the system MUST still append a history entry with null values for `filename`, `contents`, and `confidence`, and MUST log a warning. The session MUST continue recording normally.

### Key Entities

- **Setup History**: An ordered, time-stamped log of setup captures within a single recording session. Contains one entry per setup change event (session start, or pit exit where contents changed). Stored as a JSON array in the session metadata file.
- **Setup History Entry**: A single record in the setup history. Fields: `timestamp` (ISO 8601), `trigger` ("session_start" | "pit_exit"), `lap` (int), `filename` (string | null), `contents` (string | null), `confidence` ("high" | "medium" | "low" | null).
- **Pit Exit Event**: A state transition detected during an active recording session: the car was inside the pit lane in a previous frame and is now outside the pit lane. This event triggers a setup re-read and comparison.
- **Setup Confidence**: A categorical label assigned to each setup history entry, reflecting how reliably the captured file represents what AC actually loaded. Determined by directory location (primary) and file count (tiebreaker). Timestamp age is not a confidence factor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A setup file found in the track-specific directory always receives a confidence of "high" or "medium", never "low", regardless of file age.
- **SC-002**: A setup file sourced exclusively from the generic car directory (fallback) always receives a confidence of "low", preserving the semantic distinction between track-specific and generic setups.
- **SC-003**: Every pit stop where the driver changes the setup produces exactly one new setup history entry in the `.meta.json`, enabling per-stint setup attribution.
- **SC-004**: Every pit stop where the driver does NOT change the setup produces no new history entry — the history list length remains unchanged after the pit stop.
- **SC-005**: A downstream tool can determine the active setup for any lap number in a session by reading only the `.meta.json`, without parsing the CSV data.
- **SC-006**: The metadata file written at session start contains a valid `setup_history` array with at least one entry, so that a game crash after session start still produces recoverable setup context.
- **SC-007**: The `setup_history` field is always a JSON array in every metadata file produced — never null, missing, or a scalar.

## Assumptions

- AC's `ac.isCarInPitlane(0)` API call reliably returns `True` when the car is physically in the pit lane and `False` otherwise. A pit exit is detected by observing a transition from `True` to `False` in consecutive frames.
- The setup file for a changed setup is saved to disk before the car physically exits the pit lane. This is the standard AC workflow: the driver makes changes in the setup screen and AC writes them to disk before the session resumes. If AC delays the write, the capture at pit exit will reflect the pre-change file; the actual change will be captured on the next pit exit.
- Content comparison (string equality on the full `.ini` text) is sufficient to determine whether a setup changed. Two setups with identical textual contents are treated as identical even if their filenames differ.
- Re-reading a setup `.ini` file at each pit exit has negligible performance cost. Setup files are small (typically under 10 KB) and pit exits are rare events; this does not affect the 20-30Hz telemetry sampling loop.
- Replacing the flat `setup_filename`, `setup_contents`, and `setup_confidence` fields with `setup_history` is a breaking change to the metadata contract defined in feature 001. Since the Phase 2 parser has not yet been built, no migration path is required. The `specs/001-telemetry-capture/contracts/meta-json.md` contract document must be updated as part of this feature's implementation to reflect the new schema.
- Lap count at pit exit is read from `ac.getCarState(0, acsys.CS.LapCount)` at the moment the pit exit is detected, consistent with how the session-end lap count is captured.
- In fallback session detection mode (sim_info unavailable), pit lane status is still available via `ac.isCarInPitlane(0)`, which does not depend on shared memory.
