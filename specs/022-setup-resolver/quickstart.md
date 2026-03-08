# Quickstart: Tiered Setup Parameter Resolver

**Branch**: `022-setup-resolver` | **Date**: 2026-03-08

## Prerequisites

- Python 3.11+ in conda env `ac-race-engineer`
- Node.js 20 LTS with npm
- Existing backend and frontend from Phases 1-8.1

## New Package: `backend/ac_engineer/resolver/`

### Module Structure

```
backend/ac_engineer/resolver/
├── __init__.py          # Public API exports
├── models.py            # ResolvedParameters, ResolutionTier, CarStatus
├── resolver.py          # resolve_parameters() — core tier evaluation
├── defaults.py          # extract_defaults() — config file parsing
└── cache.py             # Cache CRUD (get/save/invalidate)
```

### Public API

```python
from ac_engineer.resolver import (
    resolve_parameters,
    list_cars,
    get_cached_parameters,
    invalidate_cache,
    invalidate_all_caches,
    ResolvedParameters,
    ResolutionTier,
    CarStatus,
)
```

### Core Function

```python
def resolve_parameters(
    ac_install_path: Path | None,
    car_name: str,
    db_path: Path,
    session_setup: dict[str, dict[str, float | str]] | None = None,
) -> ResolvedParameters:
    """Resolve parameter ranges and defaults for a car using 3-tier strategy.

    Tier 1: Open data/ folder → setup.ini + config files
    Tier 2: Encrypted data.acd → decrypted setup.ini + config files
    Tier 3: Session setup fallback (if session_setup provided)

    Checks cache first for Tier 1/2 results. Caches new Tier 1/2 results.
    Never raises — always returns a valid ResolvedParameters.
    """
```

## New API Router: `/cars`

### Route Registration

Add to `backend/api/main.py`:
```python
from api.routes.cars import router as cars_router
app.include_router(cars_router, prefix="/cars")
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/cars` | List installed cars with resolution status |
| GET | `/cars/{car_name}/parameters` | Get cached parameter data |
| DELETE | `/cars/{car_name}/cache` | Invalidate one car's cache |
| DELETE | `/cars/cache` | Invalidate all caches |

## Database Migration

Add to `_MIGRATIONS` list in `backend/ac_engineer/storage/db.py`:

```sql
CREATE TABLE IF NOT EXISTS parameter_cache (
    car_name      TEXT PRIMARY KEY,
    tier          INTEGER NOT NULL CHECK(tier IN (1, 2)),
    has_defaults  INTEGER NOT NULL DEFAULT 0,
    parameters_json TEXT NOT NULL,
    resolved_at   TEXT NOT NULL
)
```

## Integration Changes

### Engineer Pipeline (`backend/api/engineer/pipeline.py`)

Replace direct `read_parameter_ranges()` call with `resolve_parameters()`:

```python
# Before:
ranges = read_parameter_ranges(config.ac_install_path, car_name)

# After:
from ac_engineer.resolver import resolve_parameters
resolved = resolve_parameters(
    config.ac_install_path, car_name, db_path,
    session_setup=summary.active_setup_parameters,
)
ranges = resolved.parameters
```

### Engineer Response (`backend/ac_engineer/engineer/models.py`)

Add tier metadata fields to `EngineerResponse`:
```python
resolution_tier: int | None = None
tier_notice: str = ""
```

### Agent Dependencies (`backend/ac_engineer/engineer/models.py`)

Add tier field to `AgentDeps`:
```python
resolution_tier: int | None = None
```

## Frontend Changes

### Settings View Extension

Add a "Car Data" Card section to `frontend/src/views/settings/index.tsx`:
- Table listing cars with status badges
- "Invalidate" button per cached car
- "Invalidate All" button in card header

### New Hook

```typescript
// frontend/src/hooks/useCars.ts
export function useCars() {
  const { data, isLoading, error, refetch } = useQuery<CarListResponse>({
    queryKey: ["cars"],
    queryFn: () => apiGet<CarListResponse>("/cars"),
    staleTime: 60_000,
  });
  // + invalidate mutations
}
```

## Test Structure

```
backend/tests/resolver/
├── conftest.py              # Fixtures: mock car dirs, ACD archives
├── test_resolver.py         # Core resolution logic (tier evaluation)
├── test_defaults.py         # Default value extraction from config files
└── test_cache.py            # Cache CRUD operations

backend/tests/api/
└── test_cars_route.py       # API endpoint tests

frontend/tests/views/settings/
└── CarDataSection.test.tsx  # Car data management UI tests

frontend/tests/hooks/
└── useCars.test.ts          # Hook tests
```

## Running Tests

```bash
# Backend
conda activate ac-race-engineer
pytest backend/tests/resolver/ -v
pytest backend/tests/api/test_cars_route.py -v

# Frontend
cd frontend
npm run test -- tests/views/settings/CarDataSection.test.tsx
npm run test -- tests/hooks/useCars.test.ts
```
