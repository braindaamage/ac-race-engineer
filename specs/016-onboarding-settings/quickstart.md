# Quickstart: Onboarding Wizard & Settings

**Feature**: 016-onboarding-settings | **Date**: 2026-03-05

## Prerequisites

- Node.js 20 LTS+ and npm
- Python 3.11+ in conda env `ac-race-engineer`
- Rust toolchain (for Tauri)

## Setup

### Backend

```bash
conda activate ac-race-engineer
cd backend
pip install -e ".[dev]"   # if not already installed
```

### Frontend

```bash
cd frontend
npm install
# Install the new Tauri dialog plugin:
npm install @tauri-apps/plugin-dialog
```

### Tauri (Rust side)

In `frontend/src-tauri/Cargo.toml`, add:
```toml
tauri-plugin-dialog = "2"
```

In `frontend/src-tauri/src/lib.rs`, register the plugin:
```rust
.plugin(tauri_plugin_dialog::init())
```

In `frontend/src-tauri/capabilities/default.json`, add permission:
```json
"dialog:allow-open"
```

## Running

### Backend only (for API testing)

```bash
conda activate ac-race-engineer
cd backend
python -m api.server --port 57832
```

### Frontend dev (Vite only, no Tauri)

```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
# Folder picker won't work outside Tauri, but all other features work
```

### Full Tauri app

```bash
cd frontend
npm run tauri dev
```

## Testing

### Backend tests

```bash
conda activate ac-race-engineer
pytest backend/tests/ -v
# For just config-related tests:
pytest backend/tests/api/test_config_routes.py -v
```

### Frontend tests

```bash
cd frontend
npm run test
# TypeScript check:
npx tsc --noEmit
```

## Key Files to Edit

### Backend
- `backend/ac_engineer/config/models.py` — Add `api_key` and `onboarding_completed` fields
- `backend/api/routes/config.py` — Enhance validation, add new endpoints
- `backend/tests/api/test_config_routes.py` — Add tests for new functionality

### Frontend
- `frontend/src/App.tsx` — Add onboarding gate check
- `frontend/src/components/onboarding/` — New wizard components (create directory)
- `frontend/src/views/settings/index.tsx` — Replace placeholder with full form
- `frontend/src/hooks/useConfig.ts` — New TanStack Query hook for config
- `frontend/src-tauri/capabilities/default.json` — Add dialog permission
- `frontend/src-tauri/Cargo.toml` — Add dialog plugin dependency

## API Endpoints Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | /config | Fetch current config (includes onboarding_completed) |
| PATCH | /config | Update config fields (saves all wizard values on finish) |
| GET | /config/validate | Validate saved config with detailed per-field messages |
| POST | /config/validate-path | Validate an unsaved path (used by wizard) |
| POST | /config/validate-api-key | Test an API key against a provider |
