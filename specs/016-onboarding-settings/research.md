# Research: Onboarding Wizard & Settings

**Feature**: 016-onboarding-settings | **Date**: 2026-03-05

## R1: Tauri Dialog Plugin for Folder Picking

**Decision**: Use `@tauri-apps/plugin-dialog` with `open({ directory: true })` for native folder selection.

**Rationale**: Tauri v2 moved dialogs to a plugin architecture. The `open()` function with `directory: true` returns a string path (or null if cancelled). This is the official Tauri v2 approach — no alternatives exist within the Tauri ecosystem.

**Alternatives considered**:
- HTML `<input type="file" webkitdirectory>`: Browser-based, inconsistent UX across platforms, doesn't return a path string usable for validation. Rejected.
- Manual path entry only: Poor UX — users shouldn't have to type long Windows paths. Rejected as sole option, but the text input remains editable after dialog selection.

**Integration steps**:
1. `npm install @tauri-apps/plugin-dialog` in frontend/
2. Add `tauri-plugin-dialog` to Cargo.toml dependencies in src-tauri/
3. Add `"dialog:allow-open"` to capabilities/default.json permissions
4. Register plugin in src-tauri/lib.rs: `.plugin(tauri_plugin_dialog::init())`
5. Frontend call: `import { open } from "@tauri-apps/plugin-dialog"; const path = await open({ directory: true });`

## R2: API Key Validation Strategy Per Provider

**Decision**: Create a new `POST /config/validate-api-key` endpoint that makes a minimal API call per provider to verify the key is valid.

**Rationale**: Each provider has a lightweight "list models" endpoint that requires only a valid API key and returns quickly. This is the least-cost validation approach — no tokens consumed, minimal latency.

**Per-provider validation calls**:
- **Anthropic**: `GET https://api.anthropic.com/v1/models` with `x-api-key` header and `anthropic-version: 2023-06-01`
- **OpenAI**: `GET https://api.openai.com/v1/models` with `Authorization: Bearer <key>` header
- **Google Gemini**: `GET https://generativelanguage.googleapis.com/v1beta/models?key=<key>`

**Error distinction** (FR-027):
- HTTP 401/403 → "Invalid API key. Please check the key and try again."
- Network timeout/connection refused → "Could not reach the provider. Check your internet connection."
- HTTP 429 → "Rate limited. The key appears valid but the provider is throttling requests. Try again in a moment."
- Other errors → "Unexpected error: {status_code}. The key may be valid but the provider returned an error."

**Alternatives considered**:
- Making a tiny completion call: Consumes tokens (even if minimal), slower. Rejected.
- Client-side key format validation only: Insufficient — format-valid keys can still be revoked or from wrong accounts. Rejected as sole validation, but can be used as a pre-flight check.

## R3: Onboarding State Detection

**Decision**: Add `onboarding_completed: bool = False` to ACConfig. Frontend checks this field from `GET /config` response on app launch.

**Rationale**: The simplest approach — a single boolean in the existing config file. No separate state file, no DB table, no browser storage (prohibited by Constitution XII). The flag is set to `true` when the user clicks "Finish" in the wizard (via `PATCH /config`).

**Detection flow**:
1. App launches → splash screen while backend starts
2. Backend ready → App.tsx fetches `GET /config`
3. If `onboarding_completed === false` → render OnboardingWizard instead of AppShell
4. User completes wizard → `PATCH /config` with all fields + `onboarding_completed: true`
5. On success → transition to AppShell (Sessions view)

**Edge cases**:
- Config file missing/corrupted: `read_config()` already returns defaults (all None, `onboarding_completed: false`) → wizard shown. Correct behavior.
- Config file exists but `onboarding_completed` not present: Pydantic default `False` → wizard shown. Correct for upgrades from pre-7.2.

**Alternatives considered**:
- Checking if `ac_install_path` is non-null as proxy for "configured": Fragile — user could have an old config with a path but no API key. A dedicated flag is explicit and unambiguous. Rejected.
- Separate `.onboarding_done` sentinel file: Adds filesystem complexity for no benefit. Rejected.

## R4: Enhanced Path Validation Messages

**Decision**: Enhance `GET /config/validate` to return per-field objects with `status` and `message` instead of flat booleans. Add a new `POST /config/validate-path` endpoint for on-demand validation of paths not yet saved.

**Rationale**: The spec requires specific, actionable messages (FR-018, SC-004). The current endpoint returns only booleans — insufficient for the wizard's inline feedback. A separate path validation endpoint is needed because the wizard validates paths before saving config.

**Validation logic for AC install path**:
1. Path is empty → `{ status: "empty", message: "Please provide the path to your Assetto Corsa installation." }`
2. Path does not exist on disk → `{ status: "not_found", message: "Folder not found at this location." }`
3. Path exists but missing `content/` → `{ status: "warning", message: "This folder doesn't appear to contain Assetto Corsa. Expected to find a 'content' subfolder." }`
4. Path has `content/` but missing `content/cars/` → `{ status: "warning", message: "Found 'content' folder but 'content/cars' is missing. This may not be a complete AC installation." }`
5. Path has `content/cars/` and `content/tracks/` → `{ status: "valid", message: "Valid Assetto Corsa installation found." }`

**Validation logic for setups path**:
1. Path is empty → `{ status: "empty", message: "Please provide the path to your setup files." }`
2. Path does not exist → `{ status: "not_found", message: "Folder not found at this location." }`
3. Path exists and is a directory → `{ status: "valid", message: "Setups folder found." }`

**New endpoint**: `POST /config/validate-path` accepts `{ path: string, type: "ac_install" | "setups" }` and returns the detailed validation object. This allows the wizard to validate paths before they're saved to config.

**Alternatives considered**:
- Frontend-side path validation: Forbidden by Constitution IX — frontend must not access filesystem. All validation goes through the API. Confirmed approach.
- Only enhancing the existing GET endpoint: Insufficient — that endpoint validates the saved config. The wizard needs to validate unsaved paths during the wizard flow. Both are needed.

## R5: Wizard State Management

**Decision**: Wizard state (current step, form values, validation results) lives in React `useState` local to the `OnboardingWizard` component. No Zustand store.

**Rationale**: Per Constitution XII, `useState` is for component-local state. The wizard is a transient flow — its state doesn't need to be global or survive component unmount. Only on "Finish" does state flow to the server via `PATCH /config`. User explicitly confirmed this in planning input.

**State shape**:
```typescript
interface WizardState {
  step: 1 | 2 | 3 | 4;  // 4 = review
  acInstallPath: string;
  setupsPath: string;
  llmProvider: string;  // "anthropic" | "openai" | "gemini"
  apiKey: string;
  skippedAiStep: boolean;
}
```

**Alternatives considered**:
- Zustand store: Overkill for transient wizard state. Would pollute global state with temporary data. Rejected per user guidance and Constitution XII.
- URL-based step routing: Unnecessary — wizard is not navigable by URL. Rejected.

## R6: Settings Form Save Strategy

**Decision**: Settings form uses a "Save" button (not auto-save on blur). Changes are collected locally and sent as a single `PATCH /config` on save.

**Rationale**: The spec mentions both auto-save and explicit save — user's planning input specifies a "Save" button. Auto-save on blur is error-prone (e.g., half-typed paths would trigger validation and save). Explicit save gives the user control.

**Unsaved changes handling**: Track a `dirty` flag by comparing form state to last-fetched config. If the user navigates away while dirty, show a confirmation prompt (using the existing Modal component).

**Alternatives considered**:
- Auto-save with debounce: User guidance favors explicit save. Also, debounced auto-save of paths would trigger unnecessary backend validation calls. Rejected.
