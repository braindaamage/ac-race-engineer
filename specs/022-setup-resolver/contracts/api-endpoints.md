# API Contracts: Car Parameter Resolution

**Branch**: `022-setup-resolver` | **Date**: 2026-03-08

All endpoints are registered under the `/cars` prefix in the FastAPI router.

---

## GET /cars

List all installed cars with their resolution status.

**Query Parameters**: None

**Response** `200 OK`:
```json
{
  "cars": [
    {
      "car_name": "ks_ferrari_488_gt3",
      "status": "resolved",
      "tier": 2,
      "has_defaults": true,
      "resolved_at": "2026-03-08T14:30:00+00:00"
    },
    {
      "car_name": "ks_porsche_911_gt3_r",
      "status": "resolved",
      "tier": 1,
      "has_defaults": true,
      "resolved_at": "2026-03-07T10:15:00+00:00"
    },
    {
      "car_name": "my_custom_mod",
      "status": "unresolved",
      "tier": null,
      "has_defaults": null,
      "resolved_at": null
    }
  ],
  "total": 3
}
```

**Response** `400 Bad Request` (AC path not configured):
```json
{
  "error": {
    "type": "ac_path_not_configured",
    "message": "Assetto Corsa installation path is not configured. Set it in Settings before viewing car data.",
    "detail": null
  }
}
```

**Notes**:
- Scans `{ac_install_path}/content/cars/` for subdirectories
- Cross-references with `parameter_cache` table for resolution status
- Cars are sorted alphabetically by `car_name`
- Does not trigger resolution — read-only

---

## GET /cars/{car_name}/parameters

Get resolved parameter data for a specific car.

**Path Parameters**:
- `car_name` (string): Car folder name

**Response** `200 OK` (cached data exists):
```json
{
  "car_name": "ks_ferrari_488_gt3",
  "tier": 2,
  "has_defaults": true,
  "resolved_at": "2026-03-08T14:30:00+00:00",
  "parameters": {
    "CAMBER_LF": {
      "section": "CAMBER_LF",
      "parameter": "VALUE",
      "min_value": -4.0,
      "max_value": 0.0,
      "step": 0.1,
      "default_value": -3.0
    },
    "WING_1": {
      "section": "WING_1",
      "parameter": "VALUE",
      "min_value": 0,
      "max_value": 11,
      "step": 1,
      "default_value": 6
    }
  }
}
```

**Response** `404 Not Found` (no cached data):
```json
{
  "error": {
    "type": "not_cached",
    "message": "No cached parameter data for car 'my_custom_mod'. Run an analysis session to trigger resolution.",
    "detail": null
  }
}
```

**Notes**:
- Returns cached data only — does not trigger resolution
- For Tier 3 cars (never cached), returns 404

---

## DELETE /cars/{car_name}/cache

Invalidate cached parameter data for a specific car.

**Path Parameters**:
- `car_name` (string): Car folder name

**Response** `200 OK`:
```json
{
  "car_name": "ks_ferrari_488_gt3",
  "invalidated": true
}
```

**Response** `404 Not Found` (no cache entry):
```json
{
  "error": {
    "type": "not_cached",
    "message": "No cached data found for car 'my_custom_mod'.",
    "detail": null
  }
}
```

---

## DELETE /cars/cache

Invalidate all cached parameter data.

**Response** `200 OK`:
```json
{
  "invalidated_count": 15
}
```

**Notes**:
- This route MUST be registered before `DELETE /cars/{car_name}/cache` in the FastAPI router to prevent `"cache"` being matched as a `car_name` path parameter
- Deletes all rows from `parameter_cache` table
- Returns the count of entries that were invalidated
- Returns `{"invalidated_count": 0}` if cache was already empty (not an error)

---

## Internal Integration: Resolution During Analysis

Resolution is NOT exposed as a standalone API endpoint. It happens internally when `POST /sessions/{session_id}/engineer` triggers analysis:

1. Pipeline reads `car_name` from session metadata
2. Pipeline calls `resolve_parameters(ac_install_path, car_name, session_setup)` from the resolver module
3. Resolver checks cache → evaluates tiers → returns `ResolvedParameters`
4. Result is passed to `analyze_with_engineer()` as parameter data
5. If tier is 1 or 2 and not already cached, result is persisted to cache

This keeps resolution on-demand (FR-019) and transparent to the API consumer.

---

## Response Models (Pydantic)

```python
class CarStatusResponse(BaseModel):
    car_name: str
    status: str  # "resolved" | "unresolved"
    tier: int | None = None
    has_defaults: bool | None = None
    resolved_at: str | None = None

class CarListResponse(BaseModel):
    cars: list[CarStatusResponse]
    total: int

class CarParametersResponse(BaseModel):
    car_name: str
    tier: int
    has_defaults: bool
    resolved_at: str
    parameters: dict[str, ParameterRangeResponse]

class ParameterRangeResponse(BaseModel):
    section: str
    parameter: str
    min_value: float
    max_value: float
    step: float
    default_value: float | None = None

class CacheInvalidateResponse(BaseModel):
    car_name: str
    invalidated: bool

class CacheInvalidateAllResponse(BaseModel):
    invalidated_count: int

class ErrorDetail(BaseModel):
    type: str
    message: str
    detail: str | None = None

class CarErrorResponse(BaseModel):
    error: ErrorDetail
```
