# Feature Specification: Tiered Setup Parameter Resolver

**Feature Branch**: `022-setup-resolver`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Three-tier resolution strategy for car setup parameter data (ranges + defaults) with persistent caching and user-facing visibility of resolution status."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Parameter Resolution During Analysis (Priority: P1)

When a user triggers a session analysis for any car, the system automatically resolves the best available parameter data (ranges and defaults) for that car without requiring any user action. The resolution evaluates three tiers in order — open data folder, encrypted archive decryption, session setup fallback — and uses the first that succeeds. The AI engineer receives complete, labeled parameter data and adjusts its confidence accordingly.

**Why this priority**: This is the core behavior that replaces the current single-path lookup. Without it, the AI engineer lacks validated ranges for most official Assetto Corsa cars, limiting the quality of setup recommendations.

**Independent Test**: Can be fully tested by analyzing a session for a car with encrypted data and verifying the engineer receives parameter ranges it previously could not access. Delivers immediate value by enabling accurate setup validation for all official cars.

**Acceptance Scenarios**:

1. **Given** a car with an open `data/` folder containing `setup.ini`, **When** the system resolves parameters for that car, **Then** ranges (MIN, MAX, STEP) are read from setup.ini and default values are read from the car's physical configuration files within the data/ folder (e.g., car.ini, tyres.ini, suspensions.ini) and the result is labeled as Tier 1.
2. **Given** a car with only an encrypted `data.acd` archive (standard AC encryption), **When** the system resolves parameters, **Then** the archive is decrypted, `setup.ini` is extracted for ranges, defaults are extracted from physical configuration files within the archive (e.g., `car.ini`, `tyres.ini`, `suspensions.ini`), and the result is labeled as Tier 2.
3. **Given** a car with a `data.acd` archive encrypted with a third-party scheme (not standard AC), **When** decryption produces unreadable output, **Then** the system silently falls through to Tier 3 without error.
4. **Given** a car where neither open data nor a decryptable archive is available, **When** the system resolves parameters, **Then** it infers ranges from the active setup file associated with the session and labels the result as Tier 3.
5. **Given** a car resolved at Tier 3, **When** the AI engineer formulates its response, **Then** the response includes a notice that parameter validation is limited because complete car data was not available.
6. **Given** a car resolved at Tier 1 or Tier 2, **When** the AI engineer formulates its response, **Then** no limitation notice is included.

---

### User Story 2 - Persistent Caching of Resolved Data (Priority: P2)

When the system successfully resolves parameter data via Tier 1 or Tier 2, the result is persisted so that subsequent analyses of the same car are instant and do not repeat file I/O or decryption. Tier 3 results are never cached because they are session-specific. The cache stores the resolved data, which tier produced it, and when the resolution occurred.

**Why this priority**: Decrypting ACD archives and parsing configuration files is non-trivial work. Caching ensures this only happens once per car, making repeated analyses fast. It also provides the data foundation for the visibility features in User Story 3.

**Independent Test**: Can be tested by resolving a car's data, then resolving the same car again and verifying the second resolution returns instantly from cache without touching the filesystem.

**Acceptance Scenarios**:

1. **Given** a car resolved at Tier 1, **When** the same car is analyzed again in a later session, **Then** the cached result is returned without re-reading the filesystem.
2. **Given** a car resolved at Tier 2, **When** the same car is analyzed again, **Then** the cached result is returned without re-decrypting the archive.
3. **Given** a car resolved at Tier 3, **When** the same car is analyzed in a different session, **Then** resolution is performed fresh (no cache hit) because Tier 3 results are session-specific.
4. **Given** cached data for a car, **When** the cache entry is inspected, **Then** it contains the resolved parameter ranges, default values (if available), the tier that produced it, and the timestamp of resolution.

---

### User Story 3 - User Visibility and Cache Management (Priority: P3)

The user can view the resolution status of every car installed in their Assetto Corsa directory. For each car, they can see whether it has complete data (Tier 1 or 2), partial data (Tier 3 or not yet resolved), and when it was last resolved. The user can invalidate the cache for a specific car or for all cars, forcing re-resolution on the next analysis.

**Why this priority**: Provides transparency and control. Users who install mods or update car data need a way to force the system to re-evaluate a car's data. This is important but not blocking — the resolution and caching work without any user interaction.

**Independent Test**: Can be tested by navigating to the car data management area, verifying the list of installed cars is displayed with their resolution status, and confirming that invalidating a cached car causes fresh resolution on the next analysis.

**Acceptance Scenarios**:

1. **Given** a configured Assetto Corsa installation path, **When** the user navigates to the car data management area, **Then** they see a list of all car folders found in the installation's `content/cars/` directory.
2. **Given** the car list is displayed, **When** a car has been previously resolved and cached, **Then** its entry shows the tier used (1 or 2), whether defaults are available, and the date of last resolution.
3. **Given** the car list is displayed, **When** a car has not been resolved or was resolved at Tier 3, **Then** its entry shows an unresolved or partial status.
4. **Given** a car with cached data, **When** the user invalidates that car's cache, **Then** the next analysis of that car performs a fresh resolution.
5. **Given** multiple cars with cached data, **When** the user invalidates all caches, **Then** all cars require fresh resolution on their next analysis.
6. **Given** no Assetto Corsa installation path is configured, **When** the user navigates to the car data management area, **Then** they see a message indicating that the path must be configured first.

---

### Edge Cases

- **Open data folder exists but `setup.ini` is missing or malformed**: Tier 1 fails gracefully; the system falls through to Tier 2 (checks for `data.acd`) or Tier 3.
- **ACD archive partially decryptable — some config files absent**: Tier 2 succeeds with whatever data could be extracted. Ranges come from `setup.ini` inside the archive; defaults are populated only for parameters whose source config files were present. Missing defaults are left as null, not fabricated.
- **User invalidates cache for a car currently being analyzed**: The in-flight analysis completes with the data it already resolved. The invalidation takes effect on the next analysis.
- **Car cached at Tier 2, user later installs mod with open data folder**: The stale Tier 2 cache persists until the user manually invalidates it. After invalidation, the next resolution discovers the open data folder and caches at Tier 1.
- **Unknown car folder encountered during session analysis**: The system attempts resolution normally. If no `data/` folder and no `data.acd` exist, it falls through to Tier 3. The car folder name is taken from the session metadata, not from a pre-scanned list.
- **Assetto Corsa installation path not configured**: Resolution returns a Tier 3 result (or empty if no session setup is available). Car listing in the visibility view is unavailable and shows a configuration prompt.
- **`data.acd` file exists alongside an open `data/` folder**: Tier 1 takes precedence. The archive is never opened if the open folder provides valid data.
- **Cached data references a car folder that no longer exists on disk**: The cache entry remains valid (it stores resolved data, not file references). The user can invalidate it manually if desired.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST evaluate parameter resolution tiers in strict order: Tier 1 (open data folder) → Tier 2 (ACD archive decryption) → Tier 3 (session setup fallback).
- **FR-002**: System MUST use the first tier that produces a valid result and skip subsequent tiers.
- **FR-003**: Every resolution result MUST include: the resolved parameter data, the tier that produced it (1, 2, or 3), and whether default values are available.
- **FR-004**: Tier 1 resolution MUST read `setup.ini` from the car's open `data/` folder to extract parameter ranges (MIN, MAX, STEP), and reads default values from the car's physical configuration files in the same folder (e.g., car.ini, tyres.ini, suspensions.ini) — consistent with the approach used in Tier 2.
- **FR-005**: Tier 2 resolution MUST use the ACD reader module to decrypt the car's `data.acd` archive, extract `setup.ini` for parameter ranges, and extract default values from physical configuration files within the archive.
- **FR-006**: Tier 2 MUST detect unreadable decryption output (third-party encryption) and fall through to Tier 3 without raising an error.
- **FR-007**: Tier 3 resolution MUST infer parameter ranges from the active setup file associated with the current session, consistent with the existing behavior.
- **FR-008**: Resolution MUST never block or fail the analysis pipeline — a Tier 3 fallback is a valid outcome, not an error.
- **FR-009**: System MUST persist (cache) Tier 1 and Tier 2 resolution results so that subsequent analyses of the same car do not repeat resolution.
- **FR-010**: Cached entries MUST store: the resolved parameter data, the tier used, whether defaults are available, and the timestamp of resolution.
- **FR-011**: Tier 3 results MUST NOT be cached, since they are derived from session-specific setup files and may vary.
- **FR-012**: Cache invalidation MUST only occur through explicit user action — there is no automatic invalidation.
- **FR-013**: Users MUST be able to invalidate the cache for a single specific car.
- **FR-014**: Users MUST be able to invalidate the cache for all cars at once.
- **FR-015**: System MUST provide a view listing all car folders found in the configured Assetto Corsa installation's `content/cars/` directory, with each car's resolution status.
- **FR-016**: For each car with cached data, the view MUST display the tier used and the date of last resolution.
- **FR-017**: When the AI engineer operates on Tier 3 data, its response MUST include a notice informing the user that parameter validation is limited due to incomplete car data.
- **FR-018**: System MUST NOT re-encrypt, modify, or write to any car data files.
- **FR-019**: Resolution MUST happen on demand when a session for a car is analyzed — the system MUST NOT automatically scan all installed cars on startup.
- **FR-020**: When a Tier 1 open data folder exists alongside a `data.acd` archive, Tier 1 MUST take precedence and the archive MUST NOT be opened.
- **FR-021**: When Tier 2 successfully extracts `setup.ini` but some physical configuration files are absent from the archive, the system MUST return whatever defaults could be extracted and leave missing defaults as null.

### Key Entities

- **ResolvedParameters**: The outcome of parameter resolution for a single car. Contains the parameter ranges (with optional defaults), the tier that produced them (1, 2, or 3), whether defaults are available, and the car identifier.
- **ParameterRange** *(existing)*: A single parameter's adjustment bounds — section name, min, max, step, and optional default value.
- **ParameterCache**: Persistent store of resolved parameter data keyed by car name. Each entry includes the resolved data, tier, defaults availability flag, and resolution timestamp.
- **CarResolutionStatus**: A car's current state as presented to the user — unresolved, resolved with tier and date, or unavailable (no AC path configured).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Parameter ranges are available for 100% of official Assetto Corsa cars (those with standard encryption) after first analysis, compared to only cars with open data folders today.
- **SC-002**: Second and subsequent analyses of the same car complete parameter resolution in under 50 milliseconds (cache hit), compared to the full file I/O or decryption time on first resolution.
- **SC-003**: The AI engineer's setup change proposals for Tier 1 and Tier 2 cars include default value context (deviation from baseline) that was previously unavailable for encrypted cars.
- **SC-004**: Users can identify the resolution status of any installed car within 3 seconds of navigating to the car data management area.
- **SC-005**: When operating on Tier 3 (partial) data, 100% of engineer responses include a visible limitation notice so the user understands the reduced confidence.
- **SC-006**: Cache invalidation for a single car or all cars takes effect immediately — the next analysis performs fresh resolution.

## Assumptions

- The ACD reader module from Phase 8.1 is complete and provides a stable `read_acd(file_path, car_name) -> AcdResult` interface that returns decrypted file contents as `dict[str, bytes]`.
- The standard Assetto Corsa encryption scheme is the only scheme the system needs to support. Third-party encrypted archives are expected to fail decryption gracefully.
- Default values for setup parameters can be derived from the car's physical configuration files inside the ACD archive (e.g., `car.ini`, `tyres.ini`, `suspensions.ini`). The exact mapping of config file fields to setup parameter defaults is a design-time decision.
- The persistent cache uses the project's existing data storage location (`data/` directory or SQLite database) — the specific mechanism is an implementation decision.
- The car data management view integrates into the existing settings or a dedicated section of the desktop application — the exact UI placement is a design-time decision.
- Car names used as cache keys match the folder names in `content/cars/` and the `car_name` field in session metadata, ensuring consistent lookup.
