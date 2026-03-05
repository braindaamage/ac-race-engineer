# Feature Specification: Config, Knowledge & Packaging Endpoints

**Feature Branch**: `014-config-knowledge-endpoints`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Phase 6.5 — Expose user configuration and knowledge base as API endpoints, and verify standalone packaging for Tauri distribution."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Update Configuration (Priority: P1)

The user opens the desktop app and navigates to a settings screen. They see their current configuration: the path to their Assetto Corsa installation, the setups folder path, the LLM provider (Anthropic, OpenAI, or Gemini), and the model name. They can change any individual field — for example, switching from Anthropic to OpenAI — without re-entering the other fields. The updated configuration is persisted immediately so it survives app restarts.

**Why this priority**: Without correct configuration, no other feature works — the engineer cannot find car data, the parser cannot locate sessions, and the LLM cannot be called.

**Independent Test**: Can be fully tested by retrieving the config, updating one field, and verifying the change persists across requests.

**Acceptance Scenarios**:

1. **Given** a fresh installation with no config file, **When** the user requests the current configuration, **Then** they receive a valid response with default values (empty strings for paths, "anthropic" for provider, empty string for model).
2. **Given** an existing configuration, **When** the user updates only the LLM provider, **Then** the provider changes, all other fields remain unchanged, and the change is persisted to disk.
3. **Given** an existing configuration, **When** the user updates multiple fields at once (e.g., provider and model), **Then** all specified fields update and unspecified fields remain unchanged.
4. **Given** the user sends an update with an invalid LLM provider value, **When** the server processes the request, **Then** the update is rejected with a clear error message and no fields are modified.

---

### User Story 2 - Validate Configuration Before Running Engineer (Priority: P1)

Before the user triggers the AI engineer to analyze a session, the app checks whether the configuration is valid. The validation confirms that the AC installation path exists on disk, the setups path exists, and an LLM provider is set. The app shows the user which items pass and which fail, so they know exactly what to fix.

**Why this priority**: Prevents confusing error messages deep in the analysis pipeline by catching misconfiguration early.

**Independent Test**: Can be tested by setting up configs with valid paths, missing paths, and empty provider, then checking validation results.

**Acceptance Scenarios**:

1. **Given** a config with all valid paths and a provider set, **When** the user requests validation, **Then** the response indicates all checks pass.
2. **Given** a config where the AC install path does not exist on disk, **When** the user requests validation, **Then** the response indicates the AC path check fails while other checks reflect their actual state.
3. **Given** a config with empty paths, **When** the user requests validation, **Then** the response indicates path checks fail.

---

### User Story 3 - Search the Knowledge Base (Priority: P2)

The user types a question like "what does camber do" or "understeer causes" into a search field. The app returns relevant knowledge base sections ranked by relevance, each showing the document name, section title, and full content. This helps users learn about vehicle dynamics concepts without needing external resources.

**Why this priority**: Adds educational value and helps users understand why the engineer makes certain recommendations, but the core engineer workflow functions without it.

**Independent Test**: Can be tested by issuing search queries and verifying results contain relevant content, are ordered by relevance, and respect the result limit.

**Acceptance Scenarios**:

1. **Given** the knowledge base is loaded, **When** the user searches for "camber", **Then** they receive a list of matching sections ranked by relevance, each with document name, section title, content, and tags.
2. **Given** the knowledge base is loaded, **When** the user searches for a term with no matches (e.g., "xyznonexistent"), **Then** they receive an empty list with no error.
3. **Given** the knowledge base is loaded, **When** the user searches for a broad term that matches many sections, **Then** the results are capped at a maximum of 10 items.
4. **Given** the user sends an empty or whitespace-only query, **When** the server processes it, **Then** it returns an empty list.

---

### User Story 4 - View Knowledge Fragments for a Session (Priority: P2)

After the engineer analyzes a session and produces recommendations, the user wants to understand why those recommendations were made. They can request the knowledge fragments relevant to a specific session — the same domain knowledge the engineer consulted. The UI shows these fragments alongside the recommendations so the user can learn from the analysis.

**Why this priority**: Provides transparency into the engineer's reasoning, building user trust, but is not required for core functionality.

**Independent Test**: Can be tested by requesting fragments for an analyzed session and verifying the returned fragments correspond to the session's detected signals.

**Acceptance Scenarios**:

1. **Given** a session in "analyzed" state, **When** the user requests its knowledge fragments, **Then** they receive a list of fragments relevant to the session's detected signals.
2. **Given** a session in "engineered" state, **When** the user requests its knowledge fragments, **Then** they receive fragments (the endpoint works for both analyzed and engineered states).
3. **Given** a session in "discovered" state (not yet analyzed), **When** the user requests its knowledge fragments, **Then** the server returns an error indicating the session must be analyzed first.
4. **Given** a session ID that does not exist, **When** the user requests its knowledge fragments, **Then** the server returns a not-found error.

---

### User Story 5 - Package Server as Standalone Executable (Priority: P3)

The Phase 7 developer (building the Tauri desktop app) needs to package the Python backend as a standalone `.exe` that Tauri can launch as a sidecar process. The server must work correctly when launched from any working directory — all file paths (sessions dir, database, config file, knowledge base documents) must resolve relative to the executable location, not the current directory. A documented build process enables reproducible packaging.

**Why this priority**: Required for distribution but does not affect API functionality during development.

**Independent Test**: Can be tested by verifying the server resolves all paths correctly when launched from a different working directory than the project root.

**Acceptance Scenarios**:

1. **Given** the server is started from an arbitrary working directory, **When** it initializes, **Then** all paths (DB, sessions dir, config file, knowledge base docs) resolve correctly.
2. **Given** a PyInstaller build specification exists, **When** a developer follows the documented steps, **Then** a working `.exe` is produced that starts the server.
3. **Given** the packaged server is running, **When** the desktop app sends requests, **Then** all endpoints respond correctly.

---

### Edge Cases

- What happens when the config file is corrupted or contains invalid JSON? The system returns default configuration values (matching existing `read_config` behavior).
- What happens when the user sends unknown fields in a config update? The server rejects the request with a validation error.
- What happens when the knowledge base documents directory is missing or empty? Search returns an empty list.
- What happens when two concurrent config updates arrive? The last write wins — the config file is written atomically (existing behavior via tmp + os.replace).
- What happens when a session's analyzed data cache is missing but the DB says "analyzed"? The session signals endpoint returns an appropriate error indicating the data needs to be reprocessed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose an endpoint to retrieve the current user configuration, returning all four fields (ac_install_path, setups_path, llm_provider, llm_model) with empty strings for unset path values (never null).
- **FR-002**: System MUST expose an endpoint to partially update the user configuration, accepting any subset of fields and leaving omitted fields unchanged.
- **FR-003**: System MUST validate config updates before persisting — reject invalid LLM providers, reject unknown fields.
- **FR-004**: System MUST expose a validation endpoint that checks whether the current configuration is usable: AC path exists on disk, setups path exists on disk, LLM provider is set.
- **FR-005**: System MUST expose a keyword search endpoint for the knowledge base, returning results ranked by relevance with a maximum of 10 results.
- **FR-006**: System MUST expose an endpoint to retrieve knowledge fragments relevant to a specific analyzed session, identified by session ID.
- **FR-007**: The session knowledge endpoint MUST require the session to be in "analyzed" or "engineered" state, returning an error for sessions in other states.
- **FR-008**: All server file paths (database, sessions directory, config file, knowledge base documents) MUST resolve correctly regardless of the working directory from which the server is launched.
- **FR-009**: System MUST include a documented PyInstaller build specification for producing a standalone executable.
- **FR-010**: Knowledge search MUST return an empty list (not an error) for queries with no matches or empty queries.

### Key Entities

- **ACConfig**: User configuration with four fields: ac_install_path, setups_path, llm_provider, llm_model. Persisted as JSON on disk.
- **ConfigValidation**: Result of checking the current config's readiness — per-field status indicating which checks pass and which fail.
- **KnowledgeFragment**: A section of domain knowledge: source document name, section title, full content text, and associated tags.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view and modify all configuration fields through the app, with changes persisting across app restarts.
- **SC-002**: Configuration validation correctly identifies all invalid states (missing paths, unset provider) with per-field status.
- **SC-003**: Knowledge search returns relevant results for domain-specific queries (e.g., "understeer", "tyre pressure") in under 1 second.
- **SC-004**: Session knowledge fragments accurately reflect the signals detected in the session's analysis.
- **SC-005**: The server starts and serves all endpoints correctly when launched from any working directory.
- **SC-006**: A developer can produce a working standalone executable by following the documented build process.

## Assumptions

- The config file path is determined by the server (currently `data/config.json` relative to the project root) and is not user-configurable via the API.
- Knowledge base documents are read-only — the API does not support adding, editing, or deleting knowledge documents.
- The PyInstaller specification documents the build process but the actual `.exe` build and distribution are handled in Phase 7.
- The standalone executable bundles the knowledge base markdown documents as data files.
- Config validation is a read-only check — it does not modify the configuration.

## Out of Scope

- The actual Tauri desktop app (Phase 7).
- Building or distributing the `.exe` — only documenting and verifying the build process.
- Authentication or multi-user support.
- Modifying the knowledge base documents through the API.
- Real-time config file watching (the app reads config on demand via API calls).
