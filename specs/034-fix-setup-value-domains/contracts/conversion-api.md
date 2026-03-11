# Internal Contract: Conversion Module API

**Module**: `backend/ac_engineer/engineer/conversion.py`
**Consumers**: summarizer.py (inbound), setup_writer.py (outbound), resolver.py (classification)

## Functions

### classify_parameter

```
classify_parameter(section: str, show_clicks: int | None) -> str
```

**Input**:
- `section`: Section name from car's setup.ini (e.g., "ARB_FRONT", "CAMBER_LF", "PRESSURE_RF")
- `show_clicks`: SHOW_CLICKS field value from car's setup.ini, or None if unavailable

**Output**: One of `"index"`, `"direct"`, `"scaled"`

**Decision tree**:
- show_clicks is None → `"direct"`
- show_clicks == 2 → `"index"`
- show_clicks == 0 and section.upper().startswith("CAMBER") → `"scaled"`
- show_clicks == 0 → `"direct"`
- any other value → `"direct"`

### to_physical

```
to_physical(storage_value: float, param_range: ParameterRange) -> float
```

**Input**:
- `storage_value`: Raw value from user's setup.ini VALUE field
- `param_range`: Resolved parameter range with storage_convention set

**Output**: Physical-unit value

**Behavior by convention**:
- `None` or `"direct"` → return storage_value unchanged
- `"index"` → return param_range.min_value + storage_value × param_range.step
- `"scaled"` → return storage_value × scale_factor (0.1 for CAMBER)

### to_storage

```
to_storage(physical_value: float, param_range: ParameterRange) -> float
```

**Input**:
- `physical_value`: Physical-unit value (from LLM or user display)
- `param_range`: Resolved parameter range with storage_convention set

**Output**: Storage-format value for writing to .ini file

**Behavior by convention**:
- `None` or `"direct"` → return physical_value unchanged
- `"index"` → compute index = round((physical_value - min_value) / step), clamp to [0, max_index], return as float
- `"scaled"` → return round(physical_value / scale_factor) — rounded to nearest integer since AC stores camber as integer tenths of degree

**Index snapping**: The round() call snaps off-step physical values to the nearest valid index. The clamping ensures 0 ≤ index ≤ (max_value - min_value) / step.
**Scaled rounding**: The round() call ensures the storage value is an integer. Example: physical=-1.15 → -1.15/0.1 = -11.5 → round to -12.

## Invariants

1. **Round-trip**: `to_physical(to_storage(x, r), r) == x` within ±1e-9 for all valid physical values x
2. **Idempotence on DIRECT**: `to_physical(x, direct_range) == x` and `to_storage(x, direct_range) == x`
3. **None passthrough**: If `param_range.storage_convention is None`, both functions return their input unchanged
4. **No side effects**: Functions do not read files, access databases, or call external services

## Modified Function Signatures

### summarize_session (summarizer.py)

```
# Before:
summarize_session(session: AnalyzedSession, config: ACConfig, *, max_corner_issues: int = 5, setup_ini_contents: str | None = None) -> SessionSummary

# After:
summarize_session(session: AnalyzedSession, config: ACConfig, *, max_corner_issues: int = 5, setup_ini_contents: str | None = None, parameter_ranges: dict[str, ParameterRange] | None = None) -> SessionSummary
```

Note: All parameters after `*` are keyword-only. The new `parameter_ranges` parameter is added at the end.

### apply_changes (setup_writer.py)

```
# Before:
apply_changes(setup_path: Path, changes: list[ValidationResult]) -> list[ChangeOutcome]

# After:
apply_changes(setup_path: Path, changes: list[ValidationResult], parameter_ranges: dict[str, ParameterRange] | None = None) -> list[ChangeOutcome]
```

Both new parameters default to None for backward compatibility.
