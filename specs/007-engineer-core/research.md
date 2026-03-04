# Research: Engineer Core (Phase 5.2)

**Branch**: `007-engineer-core` | **Date**: 2026-03-04

## R1: AC Setup Parameter Range File Format

**Decision**: Parse `data/setup.ini` from the car's data directory to discover parameter ranges.

**Rationale**: Assetto Corsa uses two separate INI files both related to setups:

1. **`content/cars/<car>/data/setup.ini`** — Defines which parameters are adjustable and their ranges (MIN, MAX, STEP). This is a UI/range definition file, NOT actual setup values.
2. **`Documents/Assetto Corsa/setups/<car>/<track>/<name>.ini`** — User-saved setup files containing selected VALUES per parameter (already parsed by Phase 2).

The `data/setup.ini` format uses one section per adjustable parameter:

```ini
[CAMBER_LF]
SHOW_CLICKS=0
TAB=ALIGNMENT
NAME=Camber LF
MIN=-5.0
MAX=0.0
STEP=0.1
POS_X=0
POS_Y=0
HELP=HELP_CAMBER
```

Key fields for our reader: `MIN`, `MAX`, `STEP`. The section name (e.g., `CAMBER_LF`) matches the section name in user setup files.

**Special cases**:
- **Gear ratios**: Use `RATIOS=ratios.rto` instead of MIN/MAX/STEP, referencing an external `.rto` file. Our reader will skip gear sections or handle `.rto` files as a stretch goal.
- **SHOW_CLICKS**: When `SHOW_CLICKS=1`, the user setup VALUE is a click index and actual value = `MIN + VALUE * STEP`. When `SHOW_CLICKS=0`, VALUE is the direct physical value. Our reader stores raw MIN/MAX/STEP regardless — the interpretation is the validator's concern.

**Alternatives considered**:
- Reading `suspensions.ini`, `aero.ini`, etc. for range data — rejected because these contain physics parameters, not user-adjustable setup ranges.
- Hardcoding known parameter ranges — rejected per Constitution Principle II (Car-Agnostic Design).

## R2: Encrypted data.acd Files

**Decision**: Phase 5.2 only reads **unpacked** `data/` directories. ACD decryption is out of scope.

**Rationale**: Vanilla Kunos cars pack their data files into an encrypted `data.acd` archive using a simple ROT cipher based on the folder name. However:

1. Most mod cars ship with unpacked `data/` folders — this covers the primary use case.
2. Many players have already unpacked vanilla car data using Content Manager or other tools.
3. ACD decryption adds complexity and is a separate concern (file format reverse-engineering).
4. The spec requires returning an empty result when data is unavailable (FR-014), so missing `data/setup.ini` is handled gracefully.

A future enhancement can add ACD unpacking support. For now, the reader logs a warning when `data/setup.ini` is not found and returns empty ranges.

**Alternatives considered**:
- Implementing ACD decryption in this phase — rejected as scope creep. The ROT cipher is documented but adds an external dependency or custom crypto code.
- Bundling pre-extracted ranges for common cars — rejected per Principle II.

## R3: Value Interpretation (Clicks vs. Actual Values)

**Decision**: Store MIN/MAX/STEP as raw floats from `data/setup.ini`. The validator compares proposed values against these raw ranges. The SHOW_CLICKS mode determines how to interpret user setup file values, but the validator works with actual physical values regardless.

**Rationale**: The AI engineer will reason in physical units (degrees, bar, mm) not click counts. The summarizer already receives computed metrics in physical units. When writing changes back:

- For `SHOW_CLICKS=0`: The VALUE in the setup file is the actual value → write directly.
- For `SHOW_CLICKS=1`: The VALUE is `(actual_value - MIN) / STEP` → convert before writing.

The ParameterRange model stores the `show_clicks` flag so the writer knows which mode to use.

**Alternatives considered**:
- Always working in click space — rejected because engineers reason in physical units.
- Ignoring SHOW_CLICKS entirely — rejected because writing the wrong value format would break setups.

## R4: Atomic Write Pattern

**Decision**: Reuse the same atomic write pattern from `config/io.py`: write to `.tmp`, then `os.replace()`.

**Rationale**: This pattern is already battle-tested in the project (write_config). It's atomic on both Windows and Unix. For setup files:

1. Read original file into memory
2. Apply changes to in-memory representation
3. Write to `<path>.tmp`
4. `os.replace(<path>.tmp, <path>)` — atomic swap

Backup is a separate step that happens BEFORE the atomic write: `shutil.copy2(path, backup_path)`.

**Alternatives considered**:
- Using `tempfile.NamedTemporaryFile` — rejected because `os.replace` across different drives/volumes can fail on Windows. Using `.tmp` suffix in the same directory is safer.

## R5: Backup Naming Strategy

**Decision**: Timestamped backup files: `<name>.ini.bak.<YYYYMMDD_HHMMSS>`.

**Rationale**: The spec requires not silently overwriting previous backups (edge case). Timestamped names ensure each backup is unique. Example: `my_setup.ini.bak.20260304_153000`.

Using `datetime.now()` with second-precision is sufficient — setup changes happen at human timescales, not milliseconds.

**Alternatives considered**:
- Rotating backups (keep last N) — more complex, less transparent to the user.
- Single `.bak` file (overwrite previous) — violates spec edge case requirement.

## R6: Corner Issue Severity Scoring

**Decision**: Severity is computed as the absolute deviation of the relevant metric from its ideal value, normalized to a 0-1 scale. Corner issues are sorted by severity descending and truncated to `max_corner_issues` (default 5).

**Rationale**: The spec says "prioritized by severity" and defines severity as "how far a metric deviates from ideal." For understeer_ratio, the ideal is 1.0, so severity = `|understeer_ratio - 1.0|`. For other corner metrics (e.g., apex speed variance), severity is the raw variance value normalized.

This keeps the scoring deterministic and simple — no weights or tuning parameters.

**Alternatives considered**:
- Weighted multi-factor severity scoring — rejected as over-engineering for this phase.
- Using knowledge base signal thresholds as severity boundaries — interesting but couples two independent modules.

## R7: Session Summary Token Budget

**Decision**: Target < 2,000 tokens for a 20-lap session summary. Achieve this by:
- Including only flying laps (not all laps)
- Reporting per-wheel averages as 4 floats, not per-zone breakdowns
- Capping corner issues at 5
- Using compact field names in the Pydantic model
- Omitting None/empty fields in serialization

**Rationale**: SC-002 requires < 2,000 tokens. A typical LLM tokenizer converts ~4 characters to 1 token. A 20-lap summary with 10 flying laps, 2 stints, 5 corner issues, and session averages should fit in ~1,200-1,500 tokens when serialized as JSON with `exclude_none=True`.

**Alternatives considered**:
- Custom text serialization format — rejected in favor of standard JSON (Pydantic's `model_dump(exclude_none=True)` is simple and sufficient).
