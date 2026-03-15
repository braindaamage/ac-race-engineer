# Data Model: Fix Setup Value Domain Conversion

**Feature Branch**: `034-fix-setup-value-domains` | **Date**: 2026-03-11

## Entity Changes

### StorageConvention (NEW — string enum/constant)

Classification of a parameter's storage format. Determined at resolution time from car data only.

| Value     | Condition                                           | Conversion                              |
|-----------|-----------------------------------------------------|-----------------------------------------|
| `"index"` | SHOW_CLICKS=2                                       | physical = MIN + INDEX × STEP           |
| `"direct"`| SHOW_CLICKS=0, section NOT starting with "CAMBER"   | physical = storage (no conversion)      |
| `"scaled"`| SHOW_CLICKS=0, section starts with "CAMBER"         | physical = storage × 0.1               |
| `"direct"`| SHOW_CLICKS missing, unknown, or any other value    | physical = storage (no conversion)      |

### ParameterRange (MODIFIED — add 2 fields)

Existing Pydantic v2 model at `backend/ac_engineer/engineer/models.py`.

| Field (existing)   | Type              | Notes                |
|--------------------|-------------------|----------------------|
| section            | str               | e.g., "ARB_FRONT"   |
| parameter          | str               | Always "VALUE"       |
| min_value          | float             | Physical-unit min    |
| max_value          | float             | Physical-unit max    |
| step               | float             | Physical-unit step   |
| default_value      | float \| None     | Physical-unit default|

| Field (NEW)        | Type              | Notes                                    |
|--------------------|-------------------|------------------------------------------|
| show_clicks        | int \| None       | Raw SHOW_CLICKS from car setup.ini. None for Tier 3 or legacy cache entries. Default: None. |
| storage_convention | str \| None       | Computed: "index", "direct", or "scaled". None for Tier 3. Default: None. |

**Backward compatibility**: Both new fields default to None, so existing serialized data (JSON cache, test fixtures) remains valid. None means "no conversion" (DIRECT treatment).

**Validation**: `storage_convention` is derived from `show_clicks` and `section` name. It can be set at construction time or computed lazily. If `show_clicks` is None, `storage_convention` must be None (Tier 3 passthrough).

### Scale Factor Lookup (NEW — module constant)

Mapping from section name prefix to scale factor for SCALED parameters.

| Section Prefix | Scale Factor | Unit Conversion             |
|----------------|--------------|-----------------------------|
| `"CAMBER"`     | 0.1          | tenths of degree → degrees  |

Stored as a dict constant in conversion.py. Used by `classify_parameter()` and conversion functions.

## Conversion Functions (NEW)

Pure functions in `backend/ac_engineer/engineer/conversion.py`:

### classify_parameter(section: str, show_clicks: int | None) → str

Returns `"index"`, `"direct"`, or `"scaled"` based on decision tree from FR-001.

### to_physical(storage_value: float, param_range: ParameterRange) → float

| Convention | Formula                        | Example                           |
|------------|--------------------------------|-----------------------------------|
| index      | min + storage_value × step     | 25500 + 2 × 4500 = 34500         |
| scaled     | storage_value × scale_factor   | -18 × 0.1 = -1.8                 |
| direct     | storage_value (unchanged)      | 18 → 18                          |
| None       | storage_value (unchanged)      | passthrough for Tier 3            |

### to_storage(physical_value: float, param_range: ParameterRange) → float

| Convention | Formula                                    | Example                                |
|------------|--------------------------------------------|----------------------------------------|
| index      | round((physical - min) / step), clamped    | round((30000-25500)/4500) = 1          |
| scaled     | round(physical / scale_factor)             | round(-1.0 / 0.1) = -10               |
| direct     | physical (unchanged)                       | 16 → 16                               |
| None       | physical (unchanged)                       | passthrough for Tier 3                 |

## Cache Impact

The `parameter_cache` table stores ParameterRange data as a JSON blob. After this change:

- **New cache entries**: Include `show_clicks` and `storage_convention` fields in JSON.
- **Old cache entries**: Deserialize with `show_clicks=None` and `storage_convention=None` (Pydantic defaults). Detected as stale by `get_cached_parameters()`, which returns None to trigger re-resolution.

No schema migration needed — the JSON blob format is self-describing via Pydantic model.
