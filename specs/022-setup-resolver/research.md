# Research: Tiered Setup Parameter Resolver

**Branch**: `022-setup-resolver` | **Date**: 2026-03-08

## R-001: Default Value Extraction Strategy

**Decision**: Use a best-effort pattern-matching approach to map setup parameter sections to physical configuration file fields.

**Rationale**: Assetto Corsa's `setup.ini` defines parameter ranges (MIN, MAX, STEP) for each adjustable section (e.g., `CAMBER_LF`, `PRESSURE_RF`, `WING_1`). Default values live in the car's physical configuration files (`suspensions.ini`, `tyres.ini`, `aero.ini`, `drivetrain.ini`). The mapping between setup sections and config file fields follows AC naming conventions but is not formally documented and varies across mods.

**Approach**:
- Define a mapping table from setup.ini section name patterns to config file paths and keys:
  - `CAMBER_{corner}` → `suspensions.ini` → `[{axle}] CAMBER`
  - `TOE_OUT_{corner}` → `suspensions.ini` → `[{axle}] TOE_OUT`
  - `PRESSURE_{corner}` → `tyres.ini` → `[{axle}] PRESSURE_STATIC`
  - `SPRING_RATE_{corner}` → `suspensions.ini` → `[{axle}] SPRING_RATE`
  - `DAMP_BUMP_{corner}` → `suspensions.ini` → `[{axle}] BUMP`
  - `DAMP_FAST_BUMP_{corner}` → `suspensions.ini` → `[{axle}] FAST_BUMP`
  - `DAMP_REBOUND_{corner}` → `suspensions.ini` → `[{axle}] REBOUND`
  - `DAMP_FAST_REBOUND_{corner}` → `suspensions.ini` → `[{axle}] FAST_REBOUND`
  - `ARB_FRONT` / `ARB_REAR` → `suspensions.ini` → `[FRONT/REAR] ROD_LENGTH` or `[ARB] FRONT/REAR`
  - `WING_0` / `WING_1` → `aero.ini` → `[WING_0]/[WING_1] ANGLE`
  - `FINAL_GEAR_RATIO` → `drivetrain.ini` → `[GEARS] FINAL`
  - `GEAR_{n}` → `drivetrain.ini` → `[GEARS] GEAR_{n}`
  - `BRAKE_POWER_MULT` → `brakes.ini` → `[DATA] BASE_LEVEL`
  - `FRONT_BIAS` → `brakes.ini` → `[DATA] FRONT_SHARE`
  - `FUEL` → no config file default (session-dependent)
- Corner suffixes: `LF`→FRONT index 0, `RF`→FRONT index 1, `LR`→REAR index 0, `RR`→REAR index 1
- When a config file or key is missing, leave default as `None` — no fabrication
- The mapping is defined as a data structure (not hardcoded if/else chains) so it can be extended

**Alternatives considered**:
1. **Only use setup.ini DEFAULT field**: Simpler but many cars omit it, especially encrypted ones. This would defeat the purpose of Tier 2.
2. **Full physics model parsing**: Parse every config file exhaustively. Too complex and fragile across mod variations — overkill for extracting defaults.
3. **LLM-based mapping**: Have the AI infer defaults from config files. Violates Principle IV (LLM as interpreter, not calculator).

## R-002: Cache Storage Mechanism

**Decision**: Add a `parameter_cache` table to the existing SQLite database (`ac_engineer.db`) with JSON-serialized parameter data.

**Rationale**: The project already uses SQLite for sessions, recommendations, setup_changes, and messages. Following the same storage patterns keeps the architecture consistent. Storing resolved parameter data as a JSON blob per car (rather than one row per parameter) is more efficient because:
- Resolution produces a variable number of parameters per car (10-40+ sections)
- The entire result is always loaded/invalidated as a unit
- JSON serialization preserves the dict structure naturally

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS parameter_cache (
    car_name    TEXT PRIMARY KEY,
    tier        INTEGER NOT NULL CHECK(tier IN (1, 2)),
    has_defaults INTEGER NOT NULL DEFAULT 0,
    parameters_json TEXT NOT NULL,  -- JSON-serialized dict[str, ParameterRange]
    resolved_at TEXT NOT NULL
);
```

**Alternatives considered**:
1. **File-based cache (JSON files per car)**: Works but adds a second persistence layer alongside SQLite. Would need separate cleanup logic.
2. **One row per parameter**: Normalized but requires many more rows and joins. Resolution always operates on the full set, so the join overhead adds no value.
3. **In-memory dict with periodic dump**: Doesn't survive process restarts. The sidecar backend starts/stops with the Tauri app.

## R-003: Resolver Module Location

**Decision**: Create a new `backend/ac_engineer/resolver/` package as a peer to `engineer/`, `parser/`, `acd_reader/`, etc.

**Rationale**: The resolver orchestrates multiple existing modules (setup_reader, acd_reader, storage) and introduces new logic (default extraction, tier evaluation, caching). Placing it inside `engineer/` would conflate resolution (data acquisition) with reasoning (AI agents). A separate package follows the existing pattern where each major capability is its own package.

**Module structure**:
```
backend/ac_engineer/resolver/
├── __init__.py          # Public API: resolve_parameters, list_cars, invalidate_cache
├── models.py            # ResolvedParameters, ResolutionTier enum, CarStatus
├── resolver.py          # Core tier evaluation logic
├── defaults.py          # Default value extraction from config files
└── cache.py             # SQLite cache read/write (uses storage.db._connect)
```

**Alternatives considered**:
1. **Extend setup_reader.py**: The existing file is focused and small (~60 lines). Adding 3-tier resolution, caching, and default extraction would make it a monolith.
2. **Put in storage/**: Storage is for CRUD operations, not domain logic like tier evaluation and file parsing.

## R-004: Integration Point for Tier Notice

**Decision**: Add `resolution_tier` and `tier_notice` fields to `EngineerResponse`. Inject the notice in `analyze_with_engineer()` after resolution, before agent execution.

**Rationale**: The tier notice needs to appear in the engineer's response to the user. Adding it to `EngineerResponse` means it flows naturally through the existing serialization pipeline to the API and frontend. The notice is constructed by the resolver, not by the LLM — it's deterministic text.

**Implementation**:
1. `analyze_with_engineer()` calls the resolver instead of `read_parameter_ranges()` directly
2. The resolver returns `ResolvedParameters` which includes tier level and parameter data
3. If tier == 3, `analyze_with_engineer()` sets `tier_notice` on the response
4. The `tier_notice` field in `EngineerResponse` carries the notice as a separate field — it is not mixed into the `explanation` field produced by the LLM.
5. `AgentDeps` gains a `resolution_tier` field so tools can reference it

**Alternatives considered**:
1. **Inject notice via LLM system prompt**: The LLM might not reliably include it. Deterministic injection is more reliable.
2. **Prepend to explanation field**: Mixes deterministic text with LLM output, making it harder to render or strip in the frontend. A separate field is cleaner.

## R-005: Car Listing Strategy

**Decision**: List cars by scanning `content/cars/` directory on demand. Cross-reference with the cache table to determine resolution status.

**Rationale**: The spec requires listing all installed cars with their resolution status (FR-015). Scanning the filesystem is the only reliable way to discover installed cars (mods can be added/removed at any time). The scan is lightweight — just listing directory names, not opening files.

**Implementation**:
1. `GET /cars` scans `{ac_install_path}/content/cars/` for subdirectories
2. For each car folder, check the `parameter_cache` table for a cached entry
3. Return a merged list: car name + cache status (tier, resolved_at, has_defaults) or "unresolved"
4. If `ac_install_path` is not configured, return an error response (not a 500 — a structured response indicating the path is needed)

**Alternatives considered**:
1. **Pre-scan on startup**: Violates FR-019 (no automatic scanning on startup). Also delays startup for users with many mods.
2. **Cache the car list itself**: Stale if user installs/removes mods between scans. Filesystem scan is fast enough for directory listing.

## R-006: Frontend Placement

**Decision**: Add a "Car Data" Card section to the existing Settings view, placed between "Appearance" and "Advanced" cards.

**Rationale**: The car data management (listing cars, viewing resolution status, invalidating cache) is a settings-adjacent concern — it's system configuration, not a primary workflow. Adding it as a new Card in Settings keeps the navigation simple and follows the existing pattern of Card-based sections. A separate view would be overkill for what is essentially a status table with action buttons.

**Alternatives considered**:
1. **Separate "Car Data" view in sidebar**: Adds a 6th top-level view. The interaction is too simple (list + invalidate) to justify its own view.
2. **Inline in Analysis view**: The resolution status is relevant during analysis but managing it (invalidation) belongs in settings.
