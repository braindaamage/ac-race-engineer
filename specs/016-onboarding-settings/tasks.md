# Tasks: Onboarding Wizard & Settings

**Input**: Design documents from `/specs/016-onboarding-settings/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — project quality gates require tests for all backend endpoints and frontend components.

**Organization**: Tasks grouped by user story. US1 (Wizard) and US2 (Path Validation) are combined into one phase since they are both P1 and tightly coupled — the wizard is the primary consumer of path validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install Tauri dialog plugin and prepare project for new components

- [x] T001 Install @tauri-apps/plugin-dialog: run `npm install @tauri-apps/plugin-dialog` in frontend/
- [x] T002 Add tauri-plugin-dialog to Rust dependencies in frontend/src-tauri/Cargo.toml and register plugin in frontend/src-tauri/src/lib.rs with `.plugin(tauri_plugin_dialog::init())`
- [x] T003 Add `"dialog:allow-open"` permission to frontend/src-tauri/capabilities/default.json
- [x] T004 Create frontend/src/components/onboarding/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend model changes and shared frontend infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Backend model & endpoint changes

- [x] T005 Add `api_key: str | None = None` and `onboarding_completed: bool = False` fields to ACConfig in backend/ac_engineer/config/models.py — include empty-string-to-None validator for api_key and update `_serialize` method
- [x] T006 Update ConfigResponse and ConfigUpdateRequest in backend/api/routes/config.py — add `api_key: str` (masked), `onboarding_completed: bool` fields; update `_config_to_response` helper to mask api_key (show first 4 + last 4 chars, `****` in between, or empty string if None)
- [x] T007 Add PathValidationResult Pydantic model (`status: str`, `message: str`) and `POST /config/validate-path` endpoint in backend/api/routes/config.py — implement ac_install validation (check content/cars, content/tracks subfolders) and setups validation (check directory exists) per contracts/config-endpoints.md rules
- [x] T008 Enhance `GET /config/validate` endpoint in backend/api/routes/config.py — replace flat-boolean ConfigValidationResponse with nested per-field PathValidationResult objects, add onboarding_completed field; update response model per contracts/config-endpoints.md
- [x] T009 Update existing backend tests in backend/tests/api/test_config_routes.py — fix assertions broken by ConfigResponse new fields (api_key, onboarding_completed) and ConfigValidationResponse structural change (flat booleans → nested objects)
- [x] T010 [P] Add backend tests for POST /config/validate-path in backend/tests/api/test_config_routes.py — test all 5 ac_install conditions (empty, not_found, no content, partial content, valid) and all 3 setups conditions (empty, not_found, valid)
- [x] T011 [P] Add backend tests for api_key and onboarding_completed in PATCH /config in backend/tests/api/test_config_routes.py — test saving api_key, reading it back masked, setting onboarding_completed to true, default false on fresh config

### Frontend shared infrastructure

- [x] T012 [P] Create TypeScript types for config API responses in frontend/src/lib/validation.ts — PathValidationResult, ConnectionTestResult, ConfigResponse (with api_key and onboarding_completed), ConfigUpdateRequest, ValidatePathRequest
- [x] T013 Create useConfig hook in frontend/src/hooks/useConfig.ts — TanStack Query wrapper: GET /config with queryKey ["config"] and staleTime 60_000; PATCH /config mutation that invalidates ["config"] on success; export config, isLoading, error, updateConfig, isUpdating

**Checkpoint**: Foundation ready — backend serves new fields, frontend can fetch/update config

---

## Phase 3: User Story 1 + User Story 2 — Onboarding Wizard with Path Validation (Priority: P1) MVP

**Goal**: First-run detection shows a multi-step wizard; path inputs validate with specific, helpful messages; wizard saves config on finish and never appears again

**Independent Test**: Launch app with no config file → wizard appears → walk through steps 1-2 (paths) → skip step 3 → finish → config saved with onboarding_completed: true → restart → wizard does not appear

### Implementation

- [x] T014 [P] [US1+US2] Create PathInput component in frontend/src/components/onboarding/PathInput.tsx — text input + "Browse" button (calls Tauri `open({ directory: true })`); debounced (500ms) POST /config/validate-path on value change; display inline validation result (success/warning/error icons + colored message using design tokens); fire onValidationChange callback; hide Browse button in non-Tauri environments; CSS class prefix `ace-path-input`
- [x] T015 [P] [US1+US2] Create StepAcPath component in frontend/src/components/onboarding/StepAcPath.tsx — heading "Where is Assetto Corsa installed?", explanation text, PathInput with pathType="ac_install", Next button (always enabled, validation is advisory)
- [x] T016 [P] [US1+US2] Create StepSetupsPath component in frontend/src/components/onboarding/StepSetupsPath.tsx — heading "Where are your setup files?", explanation text, PathInput with pathType="setups", pre-fill with `{acInstallPath}/setups` when acInstallPath is set, Next and Back buttons
- [x] T017 [P] [US1] Create StepReview component in frontend/src/components/onboarding/StepReview.tsx — heading "Review your configuration", summary cards for AC path, setups path, and AI provider; re-validate paths on mount via PathInput with onValidationChange and show amber warnings if status is "warning" or "not_found"; "Edit" links to navigate back to relevant step; "Finish" button with isSaving loading state; Back button
- [x] T018 [US1] Create OnboardingWizard component in frontend/src/components/onboarding/OnboardingWizard.tsx — manage WizardState via useState (step 1-4, acInstallPath, setupsPath, llmProvider, apiKey, skippedAiStep); render step components based on current step; on "Finish" call PATCH /config via useConfig.updateConfig with all fields + onboarding_completed: true; call onComplete prop on success
- [x] T019 [US1] Create OnboardingWizard.css in frontend/src/components/onboarding/OnboardingWizard.css — styles for wizard container, step layout, navigation buttons, progress indicator; use design tokens only (no hardcoded colors); ace-onboarding prefix
- [x] T020 [US1] Modify App.tsx in frontend/src/App.tsx — after backend is ready, fetch config via useConfig; if onboarding_completed is false render OnboardingWizard with onComplete that triggers config refetch; if true render AppShell; show brief loading state while config is being fetched
- [x] T021 [P] [US1+US2] Add frontend tests for PathInput in frontend/tests/components/onboarding/PathInput.test.tsx — test: renders input and browse button; fires onChange on input; calls POST /config/validate-path (mocked) on debounced input; displays validation success/warning/error messages; fires onValidationChange callback
- [x] T022 [P] [US1] Add frontend tests for OnboardingWizard in frontend/tests/components/onboarding/OnboardingWizard.test.tsx — test: renders Step 1 initially; navigates forward/backward preserving state; "Finish" calls PATCH /config with onboarding_completed: true; calls onComplete on success
- [x] T023 [P] [US1] Add frontend tests for App onboarding gate in frontend/tests/App.test.tsx — test: shows wizard when onboarding_completed is false; shows AppShell when onboarding_completed is true; transitions from wizard to AppShell after completion

**Checkpoint**: Fresh install shows wizard → user configures paths → finishes → sees Sessions view. Restart does not show wizard again. Path validation shows specific messages for all conditions.

---

## Phase 4: User Story 3 — AI Provider Configuration (Priority: P2)

**Goal**: Wizard Step 3 lets user select AI provider, enter API key (masked), test connection, or skip; backend validates API keys against real provider endpoints

**Independent Test**: In wizard Step 3, select Anthropic, enter a key, click "Test Connection" → see success/failure; alternatively click "Skip" → review screen shows amber notice

### Backend

- [x] T024 [US3] Add ConnectionTestResult model and POST /config/validate-api-key endpoint in backend/api/routes/config.py — accept provider + api_key; make minimal GET request to provider's list-models endpoint (Anthropic: /v1/models with x-api-key header, OpenAI: /v1/models with Bearer auth, Gemini: /v1beta/models?key=); 10s timeout; return valid/message distinguishing auth failure (401/403), network error, rate limit (429), and other errors per contracts/config-endpoints.md
- [x] T025 [P] [US3] Add backend tests for POST /config/validate-api-key in backend/tests/api/test_config_routes.py — mock httpx/aiohttp calls; test: valid key returns valid=true, 401 returns valid=false with auth message, timeout returns valid=false with network message, 429 returns valid=false with rate limit message, invalid provider returns valid=false

### Frontend

- [x] T026 [US3] Create StepAiProvider component in frontend/src/components/onboarding/StepAiProvider.tsx — heading "Connect an AI provider", explanation text, provider selector (Anthropic Claude / OpenAI / Google Gemini), masked API key input with show/hide toggle, "Test Connection" button calling POST /config/validate-api-key with loading state and result display, "Skip for now" button with notice text, Next and Back buttons
- [x] T027 [US3] Wire StepAiProvider into OnboardingWizard in frontend/src/components/onboarding/OnboardingWizard.tsx — render StepAiProvider for step 3; pass provider, apiKey, onProviderChange, onApiKeyChange, onSkip (sets skippedAiStep=true and advances to step 4); update StepReview to show amber notice when skippedAiStep is true ("Engineer feature won't work without AI configuration")
- [x] T028 [P] [US3] Add frontend tests for StepAiProvider in frontend/src/components/onboarding/__tests__/StepAiProvider.test.tsx — test: renders provider selector and key input; key is masked by default; toggle reveals key text; "Test Connection" calls POST /config/validate-api-key (mocked) and shows result; "Skip" calls onSkip

**Checkpoint**: Wizard has all 4 steps functional. AI provider can be configured or skipped. Test Connection validates keys against providers.

---

## Phase 5: User Story 4 — Settings Screen (Priority: P2)

**Goal**: Replace placeholder SettingsView with full configuration form; all wizard fields editable; Save button persists changes; Re-run onboarding launches pre-filled wizard; theme toggle preserved

**Independent Test**: After onboarding, navigate to Settings → all values shown → change AC path → Save → restart app → new path persisted

### Implementation

- [x] T029 [US4] Replace SettingsView in frontend/src/views/settings/index.tsx — full settings form with 4 sections: (1) Assetto Corsa (AC install path + setups path via PathInput), (2) AI Provider (provider selector + masked API key input + Test Connection button), (3) Appearance (theme toggle preserved from Phase 7.1), (4) Advanced ("Re-run onboarding" button); initialize form from useConfig; track dirty state by comparing form values to fetched config
- [x] T030 [US4] Create Settings.css in frontend/src/views/settings/Settings.css — styles for settings layout, section cards, form fields, save button; use design tokens only; ace-settings prefix
- [x] T031 [US4] Add Save button and unsaved-changes guard in frontend/src/views/settings/index.tsx — "Save" button at bottom (disabled when not dirty, shows loading while saving); on save call useConfig.updateConfig with changed fields; show success toast via notificationStore; if user navigates to another sidebar section while dirty, show Modal confirmation ("You have unsaved changes. Discard?")
- [x] T032 [US4] Add "Re-run onboarding" in frontend/src/views/settings/index.tsx — button in Advanced section; on click, sets app-level state to show OnboardingWizard pre-filled with current config values; wizard onComplete returns to Settings; if user cancels (goes back on step 1), return to Settings without saving
- [x] T033 [P] [US4] Add frontend tests for SettingsView in frontend/src/views/settings/__tests__/SettingsView.test.tsx — test: renders all 4 sections with current config values; Save calls PATCH /config; dirty state tracked correctly; theme toggle still works; "Re-run onboarding" shows wizard

**Checkpoint**: Settings screen fully functional. All config values editable, saveable, and persistent. Re-run onboarding works. Theme toggle preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories, edge cases, and quality gates

- [x] T034 Handle corrupted/missing config edge case in frontend/src/App.tsx — if GET /config fails or returns unexpected shape, treat as onboarding_completed: false and show wizard; ensure no crash on missing fields
- [x] T035 Run TypeScript strict check (`npx tsc --noEmit` in frontend/) — fix any type errors; ensure zero explicit `any` without justification
- [x] T036 Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) — ensure all existing + new tests pass, no regressions from ConfigValidationResponse structural change
- [x] T037 Run full frontend test suite (`cd frontend && npm run test`) — ensure all existing + new tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1+US2 (Phase 3)**: Depends on Phase 2 — delivers MVP
- **US3 (Phase 4)**: Depends on Phase 3 (wizard shell must exist to wire in Step 3)
- **US4 (Phase 5)**: Depends on Phase 2 (useConfig hook); can start in parallel with Phase 4 but full integration needs Phase 3 wizard for "Re-run onboarding"
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (P1)**: Can start after Phase 2 — no dependencies on other stories. This IS the MVP.
- **US3 (P2)**: Depends on US1 (wizard shell exists) — adds Step 3 to existing wizard
- **US4 (P2)**: Core form can start after Phase 2 (just needs useConfig). "Re-run onboarding" feature depends on US1 wizard existing.

### Within Each Phase

- Models/endpoints before frontend consumers
- Backend tests parallel with frontend component creation (different files)
- Integration wiring after individual components exist
- Tests for each component can be written in parallel with the component

### Parallel Opportunities

**Phase 2**: T010, T011, T012 can run in parallel (different files)
**Phase 3**: T014, T015, T016, T017 can all run in parallel (separate component files); T021, T022, T023 can run in parallel (separate test files)
**Phase 4**: T025, T026, T028 can run in parallel
**Phase 5**: T033 can run in parallel with T030

---

## Parallel Example: Phase 3 (US1+US2)

```text
# Wave 1 — all step components in parallel (separate files):
T014: PathInput.tsx
T015: StepAcPath.tsx
T016: StepSetupsPath.tsx
T017: StepReview.tsx

# Wave 2 — wizard shell (depends on step components):
T018: OnboardingWizard.tsx
T019: OnboardingWizard.css

# Wave 3 — app integration (depends on wizard):
T020: App.tsx modification

# Wave 4 — all tests in parallel (separate files):
T021: PathInput.test.tsx
T022: OnboardingWizard.test.tsx
T023: App.test.tsx
```

---

## Implementation Strategy

### MVP First (US1+US2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T013)
3. Complete Phase 3: US1+US2 Wizard + Validation (T014-T023)
4. **STOP and VALIDATE**: Fresh install shows wizard → paths validated with specific messages → finish → app works → restart → no wizard
5. This is a fully functional onboarding without AI provider or Settings

### Incremental Delivery

1. Setup + Foundational → Backend ready with new fields and endpoints
2. Add US1+US2 → Wizard works with path validation → **MVP delivered**
3. Add US3 → AI provider step fills wizard gap → Test Connection works
4. Add US4 → Settings screen replaces placeholder → Full feature complete
5. Polish → Edge cases, type checks, full test suite green

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 are combined in Phase 3 because PathInput (US2) is inseparable from the wizard steps (US1) — validation is meaningless without a UI to display it
- The wizard in Phase 3 handles Step 3 (AI provider) as a simple "Skip" placeholder — full functionality added in Phase 4
- Existing Phase 7.1 tests must not regress — T036/T037 verify this
- All CSS must use design tokens from frontend/src/tokens.css — no hardcoded hex values
- All components must reuse design system (Button, Card, Badge, Modal, Toast) from frontend/src/components/ui/
