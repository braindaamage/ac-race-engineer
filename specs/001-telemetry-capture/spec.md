# Feature Specification: Telemetry Capture App

**Feature Branch**: `001-telemetry-capture`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Build a Python telemetry capture application that runs inside Assetto Corsa as an in-game app using AC's Python API. The app runs invisibly in the background during any driving session and automatically records telemetry data to structured files on disk."

## Clarifications

### Session 2026-03-02

- Q: Output file format? → A: CSV is the primary in-game format. Parquet conversion is a separate post-processing utility outside the game. AC's embedded Python (~3.3) cannot support pyarrow/fastparquet.
- Q: Sample rate control mechanism? → A: The app MUST implement an internal time-based throttle to maintain 20-30Hz sampling, since AC's acUpdate callback fires at render framerate (60-144+ fps), not at a fixed physics rate.
- Q: Additional telemetry channels needed? → A: Add individual wheel speed (4 channels: FL/FR/RL/RR) for downstream slip ratio calculation, and pit lane status flag for identifying pit stop events.
- Q: Should active setup be captured? → A: Yes. At session start, read the currently active setup file (.ini) for the selected car and store its complete contents as session metadata. Critical for correlating telemetry with setup parameters in later phases.
- Q: How should session metadata be stored alongside CSV telemetry data? → A: Separate sidecar JSON file per session (e.g., `2026-03-02_1430_car_track.meta.json` alongside the `.csv`). Keeps CSV cleanly parseable by any tool without header-skipping logic.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Telemetry Recording (Priority: P1)

As a driver, I want my telemetry data to be automatically recorded every time I drive so that I have a complete history of every session without any manual steps.

**Why this priority**: This is the core value proposition. Without automatic, reliable recording, no downstream analysis is possible. Every other feature depends on having captured data.

**Independent Test**: Can be fully tested by entering any track session in Assetto Corsa and verifying that a data file appears in the output directory after the session ends, containing timestamped telemetry samples at the expected frequency.

**Acceptance Scenarios**:

1. **Given** the app is installed and AC is running, **When** the driver enters a practice session on any track with any car, **Then** telemetry recording begins automatically within 1 second of the car being placed on track and a status indicator shows green (recording).
2. **Given** a recording session is active, **When** the session ends normally (return to menu), **Then** the data file is finalized with complete session metadata and saved to the output directory.
3. **Given** a recording session is active, **When** the driver is on track for 10 seconds, **Then** the file contains between 200 and 300 samples (20-30Hz) for that 10-second window, regardless of the game's rendering framerate.
4. **Given** the app is installed, **When** the driver enters qualifying or race sessions, **Then** recording starts automatically just as it does for practice sessions.

---

### User Story 2 - Universal Car Compatibility (Priority: P1)

As a driver who uses both official and modded cars, I want the app to capture telemetry from any car without errors so that I can use it regardless of my car collection.

**Why this priority**: Equal to P1 because the Assetto Corsa community heavily relies on mods. An app that only works with vanilla cars would be unusable for most players.

**Independent Test**: Can be tested by running sessions with at least 3 different cars (one vanilla, one popular mod, one obscure mod with minimal data channels) and verifying that each produces a valid data file.

**Acceptance Scenarios**:

1. **Given** the driver selects a vanilla car (e.g., any Kunos car), **When** a session is recorded, **Then** all standard telemetry channels are captured with valid numeric values.
2. **Given** the driver selects a modded car that does not expose turbo boost or ERS data, **When** a session is recorded, **Then** missing channels are filled with null/NaN values and the file is still valid and complete for all other channels.
3. **Given** the driver selects a modded car with non-standard physics, **When** a session is recorded, **Then** the app does not crash, does not produce corrupted data, and logs which channels were unavailable.

---

### User Story 3 - Crash-Safe Data Persistence (Priority: P2)

As a driver, I want my telemetry data to be preserved even if the game crashes mid-session so that I never lose a long session's worth of data.

**Why this priority**: Game crashes are common in AC (especially with mods). Losing 30+ minutes of data due to a crash would erode trust in the tool.

**Independent Test**: Can be tested by simulating a mid-session interruption (force-closing AC) and verifying that the partially captured data is recoverable and readable.

**Acceptance Scenarios**:

1. **Given** a recording session is in progress with at least 5 minutes of data, **When** the game crashes or is force-closed, **Then** at least 90% of the captured data up to that point is preserved in a readable file on disk.
2. **Given** the app is recording, **When** the buffer is periodically flushed, **Then** the flush operation does not cause any visible frame drops or stutter in gameplay.
3. **Given** a partial file exists from a crashed session, **When** the driver starts a new session, **Then** the old partial file is preserved (not overwritten) and a new file is created for the new session.

---

### User Story 4 - Zero-Impact Performance (Priority: P2)

As a driver, I want the telemetry capture to have no noticeable impact on game performance so that my driving experience and lap times are not affected.

**Why this priority**: AC is a racing simulator where frame timing directly affects driving feel. Any performance degradation would make the app unusable for competitive drivers.

**Independent Test**: Can be tested by comparing frame times and frame rate with the app enabled versus disabled over identical sessions, verifying no measurable difference.

**Acceptance Scenarios**:

1. **Given** the app is running and recording, **When** compared to a session without the app, **Then** there is no user-perceptible impact on frame rate or driving feel.
2. **Given** the app is recording at 20-30Hz, **When** the game is rendering at 60+ FPS, **Then** disk write operations never block the game's rendering thread.
3. **Given** a long session (60+ minutes), **When** the app has been recording continuously, **Then** memory usage does not grow unbounded (stays within a fixed buffer size).

---

### User Story 5 - Organized Session Files (Priority: P3)

As a driver who reviews past sessions, I want each session saved as a clearly named file so that I can easily find and identify recordings by date, car, and track.

**Why this priority**: Important for usability but not critical for core functionality. Poorly named files would make data management tedious but would not prevent analysis.

**Independent Test**: Can be tested by running multiple sessions with different cars and tracks, then verifying the output directory contains correctly named, individually readable files.

**Acceptance Scenarios**:

1. **Given** a session is completed on Monza with a Ferrari 488 GT3, **When** the file is saved, **Then** the filename follows the pattern `{date}_{time}_{car}_{track}.csv` (e.g., `2026-03-02_1430_ks_ferrari_488_gt3_monza.csv`).
2. **Given** two sessions are completed on the same day with the same car and track, **When** both files are saved, **Then** they have unique filenames (differentiated by time component) and neither is overwritten.
3. **Given** a car or track name contains special characters, **When** the filename is generated, **Then** special characters are sanitized to produce a valid filesystem path.

---

### User Story 6 - Visual Recording Status (Priority: P3)

As a driver, I want a small visual indicator showing whether telemetry is being recorded so that I have confidence the system is working without needing to check files.

**Why this priority**: Nice-to-have feedback mechanism. The app should work without any user attention, but a status indicator builds trust.

**Independent Test**: Can be tested by observing the in-game UI element during different app states (recording, buffering, error) and verifying the correct color is displayed.

**Acceptance Scenarios**:

1. **Given** the app is actively recording telemetry, **When** the driver looks at the app widget, **Then** a green indicator is displayed.
2. **Given** the app is performing a disk flush, **When** the driver looks at the app widget, **Then** a yellow indicator is briefly displayed during the flush operation.
3. **Given** an error occurs (e.g., disk full, write failure), **When** the driver looks at the app widget, **Then** a red indicator is displayed.
4. **Given** the app widget is visible, **When** the driver is driving normally, **Then** the widget is small and unobtrusive (does not interfere with driving visibility).

---

### Edge Cases

- What happens when the output disk is full? The app should display a red status indicator, stop recording gracefully, and not crash the game.
- What happens when the output directory does not exist at session start? The app should create the directory tree automatically.
- What happens when a session is extremely short (under 5 seconds, e.g., immediate return to pits)? The app should still save a valid file with whatever samples were collected, even if only a few.
- What happens when the driver switches cars or tracks without returning to the main menu (via AC's reset/restart)? The app should detect the new session and start a new file.
- What happens when a modded car reports physically impossible values (e.g., negative tyre temperatures, speed of 999999 km/h)? The app should record the raw values as-is (no filtering at capture stage) since analysis is out of scope.
- What happens when the configured sample rate cannot be maintained (system under heavy load)? The app should capture what it can without compensating, and record the actual timestamps so downstream analysis knows the true sample intervals.
- What happens when the active setup file (.ini) cannot be read at session start (e.g., file locked, permissions issue, or car mod with no setup file)? The app should record the session without setup metadata and log a warning, rather than failing to start recording.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically begin recording telemetry data when the driver enters any track session (practice, qualifying, or race) without requiring user action.
- **FR-002**: System MUST automatically stop recording and finalize the data file when the session ends.
- **FR-003**: System MUST capture telemetry samples at a rate between 20 and 30 samples per second, using an internal time-based throttle to maintain this rate regardless of AC's rendering framerate (which may range from 60 to 144+ fps).
- **FR-004**: System MUST capture the following timing channels per sample: timestamp (milliseconds), normalized track position (0.0 to 1.0), lap count, lap time, and session time.
- **FR-005**: System MUST capture the following driver input channels per sample: throttle (0-1), brake (0-1), steering angle (degrees), gear, clutch (0-1), and handbrake.
- **FR-006**: System MUST capture the following vehicle dynamics channels per sample: speed (km/h), RPM, lateral g-force, longitudinal g-force, yaw rate, and local velocity in X/Y/Z axes.
- **FR-007**: System MUST capture tyre temperature data per sample: inner, middle, and outer temperatures for each of the four tyres (12 channels total).
- **FR-008**: System MUST capture per-tyre data per sample: pressure, slip angle, slip ratio, tyre wear, and dirty level for each of the four tyres (20 channels total).
- **FR-009**: System MUST capture suspension data per sample: travel and wheel load for each of the four corners (8 channels total).
- **FR-010**: System MUST capture world position coordinates (X, Y, Z) per sample for track mapping and racing line reconstruction.
- **FR-011**: System MUST capture car state data per sample where available: turbo boost, DRS status, ERS, fuel remaining, and damage per section.
- **FR-012**: System MUST write null or NaN values for any telemetry channel that is unavailable for the current car, and MUST log which channels are missing at session start.
- **FR-013**: System MUST write session metadata to a separate sidecar JSON file (same base filename with `.meta.json` extension) including: car name/model, track name and layout variant, session type, session start date/time, number of laps completed, ambient temperature, track temperature, app version identifier, and the complete contents of the currently active setup file (.ini) for the selected car. The CSV telemetry file contains only the column header row and data rows, with no embedded metadata.
- **FR-014**: System MUST save telemetry data files in CSV format as the primary in-game output. Parquet conversion is out of scope for the in-game app and will be handled by a separate post-processing utility running in a standard Python environment.
- **FR-015**: System MUST name output files following the pattern `{date}_{time}_{car}_{track}.csv` (e.g., `2026-03-02_1430_ks_ferrari_488_gt3_monza.csv`), sanitizing special characters in car and track names.
- **FR-016**: System MUST save output files to a configurable directory, defaulting to `Documents/ac-race-engineer/sessions/`.
- **FR-017**: System MUST periodically flush captured data to disk during the session so that at least 90% of captured data survives a game crash or force-close.
- **FR-018**: System MUST preserve partial data files from crashed sessions and not overwrite them when a new session starts.
- **FR-019**: System MUST create the output directory tree if it does not exist.
- **FR-020**: System MUST display a minimal visual status indicator: green for actively recording, yellow for buffering/flushing, and red for error conditions.
- **FR-021**: System MUST work with any car available in Assetto Corsa, including vanilla cars and community-created mods, without requiring car-specific configuration.
- **FR-022**: System MUST NOT perform blocking I/O operations on the game's main thread. All disk writes MUST use buffered I/O to avoid frame-time impact.
- **FR-023**: System MUST handle disk-full conditions gracefully by stopping recording and displaying an error indicator, without crashing the game.
- **FR-024**: System MUST detect session transitions (car/track changes, session restarts) and create a new file for each distinct session.
- **FR-025**: System MUST maintain bounded memory usage regardless of session length.
- **FR-026**: System MUST capture individual wheel speed for each of the four wheels (FL/FR/RL/RR) per sample, for downstream slip ratio calculation.
- **FR-027**: System MUST capture pit lane status (whether the car is currently in the pit lane) per sample, for identifying pit stop events during analysis.
- **FR-028**: System MUST capture lap invalidation status per sample, indicating whether the current lap has been invalidated by track limits or other penalties.

### Key Entities

- **Telemetry Session**: A continuous recording from session start to session end. Identified by car, track, date, and time. Contains metadata (including active setup), and an ordered collection of telemetry samples.
- **Telemetry Sample**: A single point-in-time capture of all available telemetry channels. Identified by its timestamp within a session. Contains between 55-75+ individual channel values depending on car capabilities.
- **Session Metadata**: Descriptive information about the session context stored in a sidecar JSON file. Includes car identity, track identity, session type, environmental conditions, timing, and the complete active setup file contents.
- **Telemetry Channel**: An individual data stream (e.g., "throttle", "FL tyre inner temperature", "FL wheel speed", "pit lane status"). Has a name, unit, and expected value range. May be unavailable for certain cars.
- **Output File Pair**: Each session produces two files: a CSV file containing telemetry data (header row + data rows only), and a `.meta.json` sidecar file containing session metadata and setup contents. Both share the same base filename and are stored in the configured output directory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every driving session in Assetto Corsa produces a corresponding data file in the output directory, with zero sessions lost under normal operating conditions.
- **SC-002**: Captured data contains between 20 and 30 samples per second of driving, with actual timestamps reflecting true capture intervals, regardless of the game's rendering framerate.
- **SC-003**: 100% of vanilla Kunos cars and at least 95% of popular community mods produce valid, non-empty data files with all available channels populated.
- **SC-004**: In the event of a game crash, at least 90% of data captured up to that point is preserved in a readable file.
- **SC-005**: The app does not perform blocking I/O on the game's main thread, resulting in no user-perceptible impact on frame rate or driving feel.
- **SC-006**: Memory usage remains stable (bounded) during sessions lasting 60 minutes or longer.
- **SC-007**: The driver can identify any past session file by date, car, and track from the filename alone, without needing to open the file.
- **SC-008**: The app requires zero user interaction to capture a complete session - install once, record forever.
- **SC-009**: Session CSV files can be read and parsed by standard data analysis tools (pandas, Excel, R) without custom preprocessing.

## Assumptions

- Assetto Corsa's embedded Python environment is approximately Python 3.3. Libraries like pyarrow and fastparquet are not available and cannot be practically installed. This is why CSV is the primary in-game output format.
- AC's `acUpdate` callback fires at the render framerate (60-144+ fps), not at a fixed physics rate. The app must implement its own time-based throttle to achieve 20-30Hz sampling.
- The driver's system has sufficient disk space for session files (estimated 2-10 MB per 30-minute session in CSV format).
- The default output directory (`Documents/ac-race-engineer/sessions/`) is writable by the user account running AC.
- "Configurable output directory" means a configuration file or constant that can be edited by the user, not a runtime UI for changing paths.
- Session type detection (practice/qualifying/race) is available through AC's shared memory or Python API.
- The app version identifier is a static string embedded in the app source code, updated manually with each release.
- The active setup file (.ini) is accessible from AC's file system at session start. If unavailable (e.g., modded car with no setup, file locked), the session records without setup metadata.
- Individual wheel speed and pit lane status are available through AC's Python API for most cars.
