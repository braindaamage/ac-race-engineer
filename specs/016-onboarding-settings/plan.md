# Implementation Plan: Onboarding Wizard & Settings

**Branch**: `016-onboarding-settings` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-onboarding-settings/spec.md`

## Summary

Phase 7.2 adds first-run onboarding and a full Settings screen to the AC Race Engineer desktop app. The backend gains two new ACConfig fields (`api_key`, `onboarding_completed`), an enhanced validation endpoint with detailed per-field messages, and a new API key connection test endpoint. The frontend renders a 4-step wizard (AC path, setups path, AI provider, review) inside the existing AppShell when `onboarding_completed` is false, then replaces the placeholder SettingsView with a fully functional configuration form. The Tauri dialog plugin is added for native folder picking.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7+ strict (frontend), Rust (Tauri shell, minimal)
**Primary Dependencies**: FastAPI, Pydantic v2 (backend); React 18, TanStack Query v5, Zustand v5, Tauri v2, @tauri-apps/plugin-dialog (frontend)
**Storage**: config.json (flat file, atomic writes via tmp+replace)
**Testing**: pytest (backend, conda env `ac-race-engineer`), Vitest (frontend)
**Target Platform**: Windows 11 desktop (Tauri app)
**Project Type**: Desktop app (Tauri + React frontend, FastAPI backend sidecar)
**Performance Goals**: Validation feedback < 1s, API key test < 5s (10s timeout)
**Constraints**: No localStorage/sessionStorage, no hardcoded colors, TypeScript strict, all colors via design tokens
**Scale/Scope**: 4 wizard screens + 1 settings screen, 2 new backend endpoints, 2 new ACConfig fields

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | No telemetry data involved |
| II. Car-Agnostic Design | N/A | No car-specific logic |
| III. Setup File Autonomy | N/A | No setup file I/O |
| IV. LLM as Interpreter | PASS | API key test is a minimal validation call, not an LLM computation |
| V. Educational Explanations | N/A | No setup recommendations |
| VI. Incremental Changes | N/A | No setup modifications |
| VII. Desktop App as Primary Interface | PASS | Wizard and Settings are frontend-only UI; all data flows through API |
| VIII. API-First Design | PASS | New fields in ACConfig model; new endpoints are thin wrappers; no business logic in routes |
| IX. Separation of Concerns | PASS | Frontend calls API for config/validation; backend handles file I/O and provider validation |
| X. Desktop App Stack | PASS | Tauri shell, React UI, localhost HTTP communication, sidecar pattern preserved |
| XI. LLM Provider Abstraction | PASS | API key test uses provider-specific SDK calls but only for validation; no Pydantic AI agent needed for a simple key check |
| XII. Frontend Architecture Constraints | PASS | Wizard state in useState (local), server state via TanStack Query, Zustand for UI state only; design system components reused; no localStorage; TypeScript strict; colors via tokens |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/016-onboarding-settings/
├── plan.md              # This file
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: data model changes
├── quickstart.md        # Phase 1: dev quickstart
├── contracts/           # Phase 1: API contracts
│   ├── config-endpoints.md
│   └── frontend-components.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   └── config/
│       ├── models.py          # MODIFY: add api_key, onboarding_completed fields
│       └── io.py              # MODIFY: add api_key to serialization, LLM_MODEL_DEFAULTS unchanged
├── api/
│   └── routes/
│       └── config.py          # MODIFY: enhance validation, add POST /config/validate-api-key
└── tests/
    └── api/
        └── test_config_routes.py  # MODIFY: add tests for new endpoints/fields

frontend/
├── src/
│   ├── components/
│   │   └── onboarding/        # NEW: wizard step components
│   │       ├── OnboardingWizard.tsx
│   │       ├── OnboardingWizard.css
│   │       ├── StepAcPath.tsx
│   │       ├── StepSetupsPath.tsx
│   │       ├── StepAiProvider.tsx
│   │       ├── StepReview.tsx
│   │       └── PathInput.tsx      # Reusable path input with browse + validation
│   ├── views/
│   │   └── settings/
│   │       ├── index.tsx          # REPLACE: full settings form
│   │       └── Settings.css       # NEW: settings styles
│   ├── hooks/
│   │   └── useConfig.ts          # NEW: TanStack Query hook for GET/PATCH /config
│   ├── lib/
│   │   └── validation.ts         # NEW: validation message interpretation
│   └── App.tsx                    # MODIFY: check onboarding_completed, render wizard or AppShell
├── src-tauri/
│   ├── capabilities/
│   │   └── default.json          # MODIFY: add dialog:allow-open permission
│   └── Cargo.toml                # MODIFY: add tauri-plugin-dialog dependency
└── package.json                   # MODIFY: add @tauri-apps/plugin-dialog
```

**Structure Decision**: Extends existing backend + frontend structure. New frontend components go in `components/onboarding/` (wizard is a distinct feature, not a view). Settings view is replaced in-place. Backend changes are minimal — two new fields in ACConfig, enhanced validation endpoint, new API key test endpoint.

## Complexity Tracking

> No violations — table not needed.
