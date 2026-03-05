# Feature Specification: Onboarding Wizard & Settings

**Feature Branch**: `016-onboarding-settings`
**Created**: 2026-03-05
**Status**: Draft
**Input**: Phase 7.2 — First-run onboarding wizard and settings screen for AC Race Engineer desktop app

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Run Onboarding Wizard (Priority: P1)

A user installs AC Race Engineer and opens it for the first time. After the backend is ready and the splash screen disappears, instead of landing on an empty Sessions view, they are greeted by a step-by-step onboarding wizard. The wizard walks them through three configuration steps: locating their Assetto Corsa installation, confirming the setups folder, and optionally setting up an AI provider. Each step explains why the information is needed in plain language. When the user finishes the wizard, their configuration is saved and they land on the Sessions view. On subsequent launches, the wizard does not appear again.

**Why this priority**: Without onboarding, the app cannot function — it has no paths to find sessions or setups, and the user has no guidance on how to configure it.

**Independent Test**: Launch the app with no existing configuration file. Verify the wizard appears, walk through all steps, confirm configuration is saved, and verify the wizard does not reappear on next launch.

**Acceptance Scenarios**:

1. **Given** a fresh install with no configuration file, **When** the app finishes loading, **Then** the onboarding wizard is displayed instead of the Sessions view.
2. **Given** the wizard is displayed on Step 1, **When** the user enters a valid Assetto Corsa path, **Then** the path is validated and a success indicator is shown.
3. **Given** Step 1 has a valid AC path, **When** the user advances to Step 2, **Then** the setups folder field is pre-filled with the default location inside the AC installation.
4. **Given** the user is on any step, **When** they click "Back", **Then** they return to the previous step with their earlier input preserved.
5. **Given** the user is on Step 3 (AI provider), **When** they choose to skip this step, **Then** they advance to the review screen and are clearly informed that the Engineer feature will not work without an AI provider configured.
6. **Given** the user is on the review screen, **When** they click "Finish", **Then** all configuration is saved, the onboarding is marked complete, and the app navigates to the Sessions view.
7. **Given** a user has completed onboarding previously, **When** they relaunch the app, **Then** the wizard does not appear and the app goes directly to the Sessions view.

---

### User Story 2 - Path Validation with Helpful Feedback (Priority: P1)

As the user types or selects a folder path in the wizard or settings, the app validates the path and provides specific, actionable feedback. For the AC installation path, the app checks for expected subfolders like `content/cars` and `content/tracks`. For the setups path, it checks that the folder exists. Validation messages are specific ("This folder doesn't appear to contain Assetto Corsa. Expected to find a 'content' subfolder.") rather than generic ("Invalid path"). A valid path shows a visual success confirmation. Invalid paths show a warning but do not block the user from continuing.

**Why this priority**: Validation prevents silent misconfiguration that would cause confusing failures later. Helpful messages reduce support burden.

**Independent Test**: Enter various valid and invalid paths in Step 1 and verify that each produces the expected specific validation message and visual indicator.

**Acceptance Scenarios**:

1. **Given** the user enters a path to a valid AC installation (contains `content/cars` and `content/tracks`), **When** validation runs, **Then** a success indicator appears with a confirmation message.
2. **Given** the user enters a path to a folder that exists but is not an AC installation, **When** validation runs, **Then** a warning appears stating which expected subfolders are missing.
3. **Given** the user enters a path that does not exist on disk, **When** validation runs, **Then** a warning appears stating the folder was not found.
4. **Given** the user enters a path that triggers a warning, **When** they click "Next", **Then** they are allowed to proceed (not blocked).
5. **Given** the setups path field, **When** the user clears it and types a new path, **Then** validation runs on each change (debounced) and shows the current status.

---

### User Story 3 - AI Provider Configuration (Priority: P2)

In Step 3 of the wizard (and in Settings), the user selects an AI provider (Anthropic Claude, OpenAI, or Google Gemini) and enters their API key. The key input field is masked by default with a toggle to reveal it. The user can optionally test the connection — the app sends a minimal validation request and reports whether the key is valid. This step is skippable in the wizard; the user is informed that the Engineer feature requires it.

**Why this priority**: The AI provider is essential for the Engineer feature but not for basic app functionality (viewing sessions, comparing setups). Skippability ensures onboarding is not blocked.

**Independent Test**: Configure an AI provider with a valid key, test the connection, verify success. Then configure with an invalid key, test, verify the error message is clear.

**Acceptance Scenarios**:

1. **Given** Step 3 of the wizard, **When** the user selects a provider from the dropdown, **Then** the selection is stored and the API key field becomes active.
2. **Given** an API key has been entered, **When** the user clicks "Test Connection", **Then** the app sends a validation request and shows a success or failure message.
3. **Given** the API key field, **When** the user types, **Then** the characters are masked (shown as dots). When they toggle visibility, the actual key text is shown.
4. **Given** Step 3 with no provider or key configured, **When** the user clicks "Skip", **Then** they advance to the review screen with a clear notice that the Engineer feature requires AI configuration.

---

### User Story 4 - Settings Screen (Priority: P2)

The Settings section (always accessible from the sidebar) displays all configuration fields from the onboarding wizard — AC install path, setups path, AI provider, API key, and theme. All fields are editable. Changes are saved when the user clicks a "Save" button. A "Re-run onboarding" button lets the user go through the wizard again for a guided experience. The theme toggle (from Phase 7.1) remains in Settings.

**Why this priority**: Settings enable the user to update their configuration at any time after initial setup, which is essential for ongoing use but secondary to the first-run experience.

**Independent Test**: After completing onboarding, navigate to Settings, change the AC install path, save, restart the app, and verify the new path persists.

**Acceptance Scenarios**:

1. **Given** onboarding is complete, **When** the user navigates to Settings, **Then** all previously configured values are displayed in their respective fields.
2. **Given** the Settings screen, **When** the user changes a field and clicks "Save", **Then** the updated value is persisted and a confirmation is shown.
3. **Given** the Settings screen, **When** the user clicks "Re-run onboarding", **Then** the onboarding wizard appears, pre-filled with current values, allowing the user to walk through and update each step.
4. **Given** the Settings screen, **When** the user changes the theme toggle, **Then** the theme changes immediately (as in Phase 7.1).
5. **Given** the Settings screen with validation errors (e.g., invalid AC path), **When** the user views the field, **Then** the same specific validation messages from the wizard are shown.

---

### Edge Cases

- What happens when the configuration file is corrupted or deleted between launches? The app detects missing or invalid configuration and shows the onboarding wizard again.
- What happens when the AC installation path becomes invalid after onboarding (e.g., the user moves or uninstalls AC)? The Settings screen shows a validation warning on the affected field; the app does not crash.
- What happens when the user enters a network path or an extremely long path? Validation handles these gracefully with an appropriate message (e.g., "Folder not found" or timeout).
- What happens when the user navigates away from Settings with unsaved changes? The user is warned before losing changes.
- What happens when the backend is not reachable during wizard path validation? The wizard waits for backend readiness (splash screen handles this); if the backend becomes unavailable mid-wizard, validation shows an appropriate error state.
- What happens when the "Test Connection" for the AI provider fails due to network issues vs. invalid key? The error message distinguishes between network errors and authentication failures.
- What happens when the user re-runs onboarding and changes the AC path but cancels before finishing? No changes are saved; the previous configuration remains intact.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect whether onboarding has been completed by checking the stored configuration for a completion flag.
- **FR-002**: System MUST display the onboarding wizard on first launch when no prior configuration exists or onboarding has not been marked complete.
- **FR-003**: System MUST NOT display the onboarding wizard on subsequent launches after it has been completed.
- **FR-004**: The onboarding wizard MUST consist of four screens: Step 1 (AC install path), Step 2 (setups path), Step 3 (AI provider + API key), and a Review/Finish screen.
- **FR-005**: Each wizard step MUST include a plain-language explanation of what the information is needed for.
- **FR-006**: The wizard MUST support free forward and backward navigation — the user can go back to any previous step without losing entered data.
- **FR-007**: Step 1 MUST accept a folder path via direct text input or a folder picker (native OS dialog).
- **FR-008**: Step 1 MUST validate the AC install path by checking for the existence of expected subfolders (`content/cars`, `content/tracks`) within the provided directory.
- **FR-009**: Step 2 MUST suggest a default setups path derived from the AC install path entered in Step 1.
- **FR-010**: Step 2 MUST allow the user to override the suggested path by typing or browsing.
- **FR-011**: Step 3 MUST present a selection of AI providers: Anthropic Claude, OpenAI, and Google Gemini.
- **FR-012**: Step 3 MUST include an API key input that is masked by default with a toggle to show/hide the key text.
- **FR-013**: Step 3 MUST include a "Test Connection" action that validates the API key by making a minimal request to the selected provider.
- **FR-014**: Step 3 MUST be skippable — the user can proceed to the review screen without configuring an AI provider.
- **FR-015**: The review screen MUST display a summary of all configured values before the user confirms.
- **FR-016**: The review screen MUST allow the user to go back and edit any step.
- **FR-017**: On wizard completion ("Finish"), the system MUST persist all configuration values and mark onboarding as complete.
- **FR-018**: Validation MUST provide specific, actionable feedback messages — not generic "invalid" errors. Messages MUST reference what was expected (e.g., expected subfolder names).
- **FR-019**: Successfully validated paths MUST show a visual success indicator (not just the absence of an error).
- **FR-020**: Paths that fail validation MUST show a warning but MUST NOT block the user from advancing to the next step.
- **FR-021**: The Settings screen MUST display all configuration fields: AC install path, setups path, AI provider, API key, and theme.
- **FR-022**: The Settings screen MUST include a "Save" button that persists all changes.
- **FR-023**: The Settings screen MUST include a "Re-run onboarding" action that launches the wizard pre-filled with current values.
- **FR-024**: The Settings screen MUST retain the existing theme toggle from Phase 7.1.
- **FR-025**: The system MUST store the API key in the application configuration alongside other settings.
- **FR-026**: The system MUST handle corrupted or missing configuration files gracefully by falling back to the onboarding wizard without crashing.
- **FR-027**: The "Test Connection" result MUST distinguish between authentication failures (invalid key) and network errors.

### Key Entities

- **Application Configuration**: The set of user-provided settings — AC install path, setups path, AI provider, AI API key, UI theme, and onboarding completion flag. Persisted to disk and read on launch.
- **Onboarding State**: Whether the user has completed the initial setup wizard. Stored as a flag within the configuration. Determines whether the app shows the wizard or the main interface on launch.
- **Path Validation Result**: The outcome of checking a filesystem path — includes a status (valid, warning, not found) and a human-readable message explaining the specific finding.
- **Connection Test Result**: The outcome of testing an API key against a provider — includes a status (success, auth failure, network error) and a descriptive message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with a fresh install can complete the onboarding wizard in under 2 minutes with valid inputs.
- **SC-002**: The wizard is shown exactly once per fresh install — never on subsequent launches after completion.
- **SC-003**: Each wizard step provides validation feedback within 1 second of the user finishing their input.
- **SC-004**: 100% of validation messages are specific — they reference expected folder names or explain the exact issue found. Zero generic "invalid" messages exist in the interface.
- **SC-005**: The user can navigate forward and backward through all wizard steps without any previously entered data being lost.
- **SC-006**: Step 3 (AI provider) can be skipped without blocking wizard completion; the user is clearly informed of the consequence.
- **SC-007**: All values configured in the wizard are immediately visible and correct in the Settings screen after completion.
- **SC-008**: Configuration changes made in Settings persist across app restarts without data loss.
- **SC-009**: The app never crashes or shows an unhandled error screen due to missing, corrupted, or partially filled configuration — it always recovers gracefully.
- **SC-010**: The "Test Connection" action returns a clear success or failure message within 5 seconds under normal network conditions.

## Assumptions

- The folder picker uses the native OS dialog provided by the desktop shell framework.
- The API key is stored in the same configuration file as other settings. Secure credential storage (OS keychain integration) is out of scope for this phase.
- The "Test Connection" feature is implemented as a backend endpoint that makes a minimal API call to the selected provider to verify the key.
- An `onboarding_completed` boolean flag is added to the configuration model to track first-run state.
- Path validation for the AC installation specifically checks for `content/cars` and `content/tracks` subfolders, consistent with the existing application logic that uses these paths.
- The default setups path suggestion follows AC's convention: `<ac_install_path>/setups`.
- The wizard does not save any configuration until the user clicks "Finish" on the review screen — partial progress is not persisted.
- When re-running onboarding from Settings, the wizard is pre-filled with current values but changes are only saved on "Finish"; cancelling preserves the original configuration.
