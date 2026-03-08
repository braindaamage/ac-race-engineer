# Data Model: Tiered Setup Parameter Resolver

**Branch**: `022-setup-resolver` | **Date**: 2026-03-08

## Entities

### ResolutionTier (Enum)

Identifies which resolution strategy produced the parameter data.

| Value | Label | Description |
|-------|-------|-------------|
| 1 | `OPEN_DATA` | Read from car's open `data/` folder |
| 2 | `ACD_ARCHIVE` | Extracted from decrypted `data.acd` archive |
| 3 | `SESSION_FALLBACK` | Inferred from session's active setup file |

**Constraints**:
- Only tiers 1 and 2 are cacheable
- Tier 3 is session-specific and always transient

---

### ResolvedParameters

The outcome of parameter resolution for a single car. This is the primary data structure returned by the resolver.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| car_name | string | yes | Car folder name (e.g., `ks_ferrari_488_gt3`) |
| tier | ResolutionTier | yes | Which tier produced this data |
| parameters | dict[string, ParameterRange] | yes | Section name → range data |
| has_defaults | boolean | yes | Whether any parameter has a non-null default |
| resolved_at | ISO 8601 string | yes | When this resolution occurred |

**Relationships**:
- Contains 0..N `ParameterRange` entries (keyed by section name)
- For tiers 1 and 2, may be persisted in `ParameterCacheEntry`
- Consumed by `AgentDeps.parameter_ranges` during engineer analysis

**Constraints**:
- `car_name` matches folder names in `content/cars/` and session metadata `car` field
- `parameters` may be empty (valid result — car has no adjustable parameters)
- `has_defaults` is `True` if at least one ParameterRange has `default_value != null`

---

### ParameterRange (existing — extended)

A single parameter's adjustment bounds. Already exists in `engineer/models.py`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| section | string | yes | Setup section name (e.g., `CAMBER_LF`) |
| parameter | string | yes | Always `VALUE` in AC setup files |
| min_value | float | yes | Minimum allowed value |
| max_value | float | yes | Maximum allowed value |
| step | float | yes | Adjustment step size |
| default_value | float or null | no | Factory default from config files |

**Changes**: No structural changes. The `default_value` field already exists but was only populated from `setup.ini`'s optional `DEFAULT` key. Now it will also be populated from physical configuration files.

---

### ParameterCacheEntry (new — SQLite)

Persisted cache entry for a resolved car. One row per car.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| car_name | string (PK) | yes | Car folder name |
| tier | integer | yes | 1 or 2 (Tier 3 never cached) |
| has_defaults | boolean | yes | Whether defaults were found |
| parameters_json | string | yes | JSON-serialized `dict[str, ParameterRange]` |
| resolved_at | string | yes | ISO 8601 timestamp of resolution |

**Constraints**:
- Primary key on `car_name` — one cache entry per car
- `tier` must be 1 or 2 (CHECK constraint)
- `parameters_json` is a JSON string; deserialized on read
- Invalidation = DELETE row(s)

**SQL Schema**:
```sql
CREATE TABLE IF NOT EXISTS parameter_cache (
    car_name    TEXT PRIMARY KEY,
    tier        INTEGER NOT NULL CHECK(tier IN (1, 2)),
    has_defaults INTEGER NOT NULL DEFAULT 0,
    parameters_json TEXT NOT NULL,
    resolved_at TEXT NOT NULL
);
```

---

### CarStatus

Presentation model for the car data management view. Not persisted — assembled at query time by cross-referencing the filesystem with the cache table.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| car_name | string | yes | Car folder name |
| status | string | yes | `resolved` or `unresolved` |
| tier | integer or null | no | 1 or 2 if resolved, null otherwise |
| has_defaults | boolean or null | no | Whether defaults available, null if unresolved |
| resolved_at | string or null | no | ISO 8601 timestamp, null if unresolved |

**Constraints**:
- When `status` is `unresolved`: `tier`, `has_defaults`, and `resolved_at` are all null
- When `status` is `resolved`: all three fields are populated

---

### EngineerResponse (existing — extended)

| New Field | Type | Required | Description |
|-----------|------|----------|-------------|
| resolution_tier | integer or null | no | Tier used for parameter resolution (1, 2, 3) |
| tier_notice | string | no | Human-readable notice if Tier 3 (empty string otherwise) |

**Defaults**: `resolution_tier = None`, `tier_notice = ""`

---

### AgentDeps (existing — extended)

| New Field | Type | Required | Description |
|-----------|------|----------|-------------|
| resolution_tier | integer or null | no | Passed through so tools can reference it |

**Default**: `resolution_tier = None`

---

## State Transitions

### Resolution Flow

```
[No Data] ──resolve()──→ [Tier 1: Open Data] ──cache──→ [Cached]
    │                          │ (fail)
    │                          ▼
    │                    [Tier 2: ACD Archive] ──cache──→ [Cached]
    │                          │ (fail)
    │                          ▼
    └─────────────────→ [Tier 3: Session Fallback] (not cached)
```

### Cache Lifecycle

```
[Empty] ──first resolution (T1/T2)──→ [Cached]
                                          │
                    ┌─────────────────────┤
                    │                     │
              invalidate_one()      invalidate_all()
                    │                     │
                    ▼                     ▼
                [Empty]              [All Empty]
                    │                     │
              next analysis          next analysis
                    │                     │
                    ▼                     ▼
                [Cached]             [Cached per car]
```

## Validation Rules

1. `ParameterRange.step` must be > 0
2. `ParameterRange.min_value` must be ≤ `ParameterRange.max_value`
3. `ParameterCacheEntry.tier` must be 1 or 2 (never 3)
4. `car_name` must be non-empty and match `[a-zA-Z0-9_-]+` pattern
5. `parameters_json` must be valid JSON deserializable to `dict[str, ParameterRange]`
