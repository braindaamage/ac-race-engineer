# Frontend Component Contracts: Onboarding Wizard & Settings

**Feature**: 016-onboarding-settings | **Date**: 2026-03-05

## Component Tree

```
App.tsx
├── SplashScreen (existing, unchanged)
├── OnboardingWizard (NEW — shown when onboarding_completed === false)
│   ├── StepAcPath
│   │   └── PathInput (reusable)
│   ├── StepSetupsPath
│   │   └── PathInput (reusable)
│   ├── StepAiProvider
│   └── StepReview
└── AppShell (existing — shown when onboarding_completed === true)
    └── SettingsView (REPLACED — full settings form)
        └── PathInput (reusable, same component)
```

## New Components

### OnboardingWizard

**Purpose**: Multi-step onboarding flow, renders instead of AppShell on first run.

**Props**:
```typescript
interface OnboardingWizardProps {
  onComplete: () => void;  // Called after successful PATCH /config
}
```

**Internal state** (useState):
```typescript
interface WizardState {
  step: 1 | 2 | 3 | 4;
  acInstallPath: string;
  setupsPath: string;
  llmProvider: "anthropic" | "openai" | "gemini";
  apiKey: string;
  skippedAiStep: boolean;
}
```

**Behavior**:
- Step navigation via Next/Back buttons; state preserved across steps.
- Step 4 (review) shows all values; "Finish" calls `PATCH /config` with all fields + `onboarding_completed: true`.
- On successful PATCH, calls `onComplete()` which triggers re-fetch of config and transition to AppShell.
- CSS class prefix: `ace-onboarding`

### PathInput

**Purpose**: Reusable path input with browse button and inline validation feedback. Used in wizard steps and Settings.

**Props**:
```typescript
interface PathInputProps {
  label: string;
  value: string;
  onChange: (path: string) => void;
  pathType: "ac_install" | "setups";
  placeholder?: string;
  helpText?: string;
  onValidationChange?: (result: PathValidationResult | null) => void;
}
```

`onValidationChange` fires after each validation response (or `null` when the field is cleared / validation is pending). This lets parent components — notably **StepReview** — access the latest validation state without duplicating API calls.

**Behavior**:
- Text input + "Browse" button (calls Tauri `open({ directory: true })`).
- On value change (debounced 500ms), calls `POST /config/validate-path`.
- Displays validation result inline: success icon + green message, warning icon + amber message, or error icon + red message.
- In non-Tauri environments (tests), Browse button is hidden or disabled.
- CSS class prefix: `ace-path-input`

### StepAcPath

**Purpose**: Wizard Step 1 — Assetto Corsa installation path.

**Props**:
```typescript
interface StepProps {
  value: string;
  onChange: (value: string) => void;
  onNext: () => void;
  onBack?: () => void;  // undefined for Step 1
}
```

**Content**:
- Heading: "Where is Assetto Corsa installed?"
- Explanation text: "We need this to find your car data, track information, and recorded sessions."
- PathInput with `pathType="ac_install"`
- "Next" button (always enabled — validation is advisory, not blocking)

### StepSetupsPath

**Purpose**: Wizard Step 2 — Setups folder path.

**Props**: Same as StepProps, plus `acInstallPath: string` for deriving the default.

**Content**:
- Heading: "Where are your setup files?"
- Explanation text: "This is where your car setup .ini files are stored. We'll read and modify setups here."
- Pre-filled with `{acInstallPath}/setups` if acInstallPath is set.
- PathInput with `pathType="setups"`
- "Next" and "Back" buttons

### StepAiProvider

**Purpose**: Wizard Step 3 — AI provider and API key (skippable).

**Props**: StepProps extended with:
```typescript
interface StepAiProviderProps extends StepProps {
  provider: string;
  onProviderChange: (provider: string) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  onSkip: () => void;
}
```

**Content**:
- Heading: "Connect an AI provider"
- Explanation text: "The Race Engineer uses AI to analyze your driving and suggest setup changes. You'll need an API key from one of these providers."
- Provider selector (3 options: Anthropic Claude, OpenAI, Google Gemini)
- API key input (masked, with show/hide toggle)
- "Test Connection" button → calls `POST /config/validate-api-key`
- "Skip for now" link/button with notice: "You can configure this later in Settings. The Engineer feature won't work without it."
- "Next" and "Back" buttons

### StepReview

**Purpose**: Wizard Step 4 — Review all configured values before finishing.

**Props**:
```typescript
interface StepReviewProps {
  acInstallPath: string;
  setupsPath: string;
  llmProvider: string;
  apiKey: string;
  skippedAiStep: boolean;
  onBack: () => void;
  onFinish: () => void;
  isSaving: boolean;
}
```

**Content**:
- Heading: "Review your configuration"
- Summary cards showing each configured value
- Path fields re-validate on mount via `POST /config/validate-path`; results are displayed inline using the `PathValidationResult` returned through `onValidationChange`. If either path has a `"warning"` or `"not_found"` status, the review card shows the validation message in amber so the user can decide whether to go back and fix it before finishing.
- If AI was skipped: amber notice that Engineer feature won't work
- "Edit" links next to each section (navigate back to relevant step)
- "Finish" button (shows loading state while saving)
- "Back" button

### SettingsView (replaced)

**Purpose**: Full settings form replacing the Phase 7.1 placeholder.

**State**: Local `useState` for form fields, initialized from `GET /config` (via TanStack Query).

**Sections**:
1. **Assetto Corsa** — AC install path (PathInput), setups path (PathInput)
2. **AI Provider** — Provider selector, API key input (masked), Test Connection button
3. **Appearance** — Theme toggle (existing, preserved from Phase 7.1)
4. **Advanced** — "Re-run onboarding" button

**Save behavior**: "Save" button at the bottom. Dirty state tracked (form values differ from fetched config). If user navigates away with unsaved changes, Modal confirmation shown.

## Hook: useConfig

**Purpose**: TanStack Query wrapper for config fetch and mutation.

```typescript
function useConfig(): {
  config: ConfigResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  updateConfig: (fields: Partial<ConfigUpdateRequest>) => Promise<ConfigResponse>;
  isUpdating: boolean;
}
```

**Query**: `GET /config` with `queryKey: ["config"]`, `staleTime: 60_000`.
**Mutation**: `PATCH /config`, invalidates `["config"]` on success.

## App.tsx Changes

**Current flow**: `status !== "ready"` → SplashScreen; else → AppShell.

**New flow**: `status !== "ready"` → SplashScreen; `onboarding_completed === false` → OnboardingWizard; else → AppShell.

The config fetch happens after backend is ready. While fetching, a brief loading state is shown (can reuse SplashScreen with a "Loading configuration..." message, or show a minimal spinner).
