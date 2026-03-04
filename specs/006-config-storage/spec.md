# Feature Specification: Config + Storage (Phase 5.1)

**Feature Branch**: `006-config-storage`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Build the persistent infrastructure layer for AC Race Engineer AI — Phase 5.1: Config + Storage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure AC Installation Path (Priority: P1)

A user installs AC Race Engineer and needs to tell it where Assetto Corsa lives on their machine. They open the tool, set the AC installation path once, and never have to set it again — even after closing and reopening the application. If they move their AC installation, they can update the path at any time without losing their other settings.

**Why this priority**: Without knowing where AC is installed, the system cannot locate telemetry files, setup files, or any game data. This is the most fundamental configuration and a prerequisite for all other functionality.

**Independent Test**: Can be fully tested by writing a configuration file with an AC path, closing the application, reopening it, and confirming the path is still set.

**Acceptance Scenarios**:

1. **Given** a fresh installation with no configuration file, **When** the user sets the AC installation path, **Then** the path is persisted to a configuration file and is available on the next application launch.
2. **Given** an existing configuration with AC path and LLM provider already set, **When** the user updates only the AC installation path, **Then** the AC path changes but the LLM provider setting remains intact.
3. **Given** a fresh installation with no configuration file, **When** the system starts, **Then** it operates with sensible defaults and does not crash.

---

### User Story 2 - Choose AI Provider (Priority: P1)

A user wants to use their preferred AI provider (e.g., Anthropic Claude, OpenAI, Google Gemini) for the race engineer conversations. They select their provider and optionally a specific model, and the system remembers this choice. They can switch providers at any time.

**Why this priority**: The AI engineer is the core value proposition. Users need to configure which LLM backs it before any engineer interactions can happen. Equal priority with US-1 since both are required for the system to function.

**Independent Test**: Can be fully tested by setting an LLM provider, restarting, and confirming the provider is still selected.

**Acceptance Scenarios**:

1. **Given** a configuration with no LLM provider set, **When** the user selects a provider, **Then** the provider is persisted and used for subsequent engineer interactions.
2. **Given** a configuration with a provider set, **When** the user changes to a different provider and optionally specifies a model, **Then** both the new provider and model are persisted.
3. **Given** a configuration with a provider and model set, **When** the user changes only the provider, **Then** only the provider field is updated — the model field is preserved as-is. The system resolves the effective model at runtime: if no model is stored, it uses the provider's default; if a model is stored, it uses that value regardless of provider.

---

### User Story 3 - Browse Past Sessions (Priority: P2)

A user has completed several track sessions over multiple days. They want to see a list of all their past sessions to find a specific one — perhaps the session at Monza last Tuesday. The list shows each session's car, track, date, lap count, and best lap time at a glance, with the most recent session at the top. They can also filter by car name to narrow down results.

**Why this priority**: Session browsing is the primary entry point for all analysis and engineer interactions. Without a session index, users must manually locate files on disk. However, it depends on the config layer being in place first.

**Independent Test**: Can be fully tested by saving three sessions with different cars/tracks, listing them, verifying order is most-recent-first, and filtering by car name.

**Acceptance Scenarios**:

1. **Given** no sessions have been saved, **When** the user requests the session list, **Then** an empty list is returned.
2. **Given** five sessions exist spanning three different cars, **When** the user requests the session list, **Then** all five sessions are returned ordered by date (most recent first), each showing car, track, date, lap count, and best lap time.
3. **Given** five sessions exist spanning three different cars, **When** the user filters by a specific car name, **Then** only sessions for that car are returned, still ordered by date.
4. **Given** a session exists with a known identifier, **When** the user looks up that session by its identifier, **Then** the full session record is returned.

---

### User Story 4 - Track Engineer Recommendations (Priority: P2)

After analyzing a session, the AI engineer suggests setup changes. The user wants to see all recommendations for that session, decide which to accept or reject, and come back later to review what was suggested. Each recommendation includes the individual parameter changes and the reasoning behind them.

**Why this priority**: Recommendations are the core output of the engineer. Persisting them enables the accept/reject workflow and prevents the user from losing suggestions if they close the app before acting on them.

**Independent Test**: Can be fully tested by saving a recommendation with parameter changes, retrieving it, and updating its status to accepted or rejected.

**Acceptance Scenarios**:

1. **Given** a session with no recommendations, **When** the engineer generates a recommendation, **Then** it is saved with status "pending" and includes all parameter changes with their reasoning.
2. **Given** a session with three pending recommendations, **When** the user retrieves recommendations for that session, **Then** all three are returned with their full detail.
3. **Given** a pending recommendation, **When** the user marks it as accepted, **Then** its status changes to "accepted" and the change is persisted.
4. **Given** a pending recommendation, **When** the user marks it as rejected, **Then** its status changes to "rejected" and the change is persisted.

---

### User Story 5 - Continue Engineer Conversations (Priority: P3)

A user starts a conversation with the AI engineer about a session, discusses understeer in turn 3, then closes the app. When they reopen it later and select the same session, the full conversation history is there — they can pick up right where they left off without repeating context.

**Why this priority**: Conversation persistence enables multi-session interactions and prevents context loss. Lower priority because the system is still useful without it (the engineer can re-analyze), but it significantly improves user experience.

**Independent Test**: Can be fully tested by saving several messages for a session, retrieving them, and verifying chronological order is preserved.

**Acceptance Scenarios**:

1. **Given** a session with no conversation history, **When** a message is saved, **Then** it is persisted with its role (user or assistant), content, and timestamp.
2. **Given** a session with five messages, **When** the user retrieves the conversation history, **Then** all five messages are returned in chronological order.
3. **Given** a session with existing conversation history, **When** the user clears the conversation, **Then** all messages for that session are deleted and subsequent retrieval returns an empty list.

---

### Edge Cases

- What happens when the configuration file is corrupted or contains invalid JSON? The system falls back to defaults without crashing.
- What happens when a configuration value has an unexpected type (e.g., a number where a string is expected)? The system ignores the invalid value and uses the default for that field.
- What happens when two processes try to write configuration simultaneously? The last write wins; no crash or data corruption occurs.
- What happens when the storage database file is missing on startup? It is created automatically with the correct schema.
- What happens when the storage database file is corrupted? The system reports an error clearly rather than silently producing wrong results.
- What happens when a session is saved with a duplicate identifier? The save operation fails gracefully with a clear error rather than silently overwriting.
- What happens when the user filters sessions by a car name that has no matches? An empty list is returned.
- What happens when updating the status of a recommendation that does not exist? The operation fails gracefully with a clear error.

## Requirements *(mandatory)*

### Functional Requirements

**Configuration:**

- **FR-001**: System MUST persist user configuration as a local file in the project's data directory (`data/config.json`).
- **FR-002**: System MUST support the following configuration fields: AC installation path, setups folder path, LLM provider name, and LLM model name.
- **FR-003**: System MUST allow reading the full configuration at any time.
- **FR-004**: System MUST allow updating individual configuration fields without affecting other fields (partial update).
- **FR-005**: System MUST allow writing a complete configuration, replacing all fields at once.
- **FR-006**: System MUST fall back to sensible defaults when the configuration file is missing, empty, or corrupted — never crash.
- **FR-007**: All configuration fields MUST be optional — the system operates (with reduced functionality) even when no fields are set.
- **FR-008**: System MUST validate configuration values on read (e.g., reject non-string types for path fields) and substitute defaults for invalid values.

**Session Storage:**

- **FR-009**: System MUST initialize the storage database automatically on first use, creating all required tables.
- **FR-010**: System MUST store session records with at minimum: unique identifier, car name, track name, session date, number of laps, and best lap time.
- **FR-011**: System MUST support saving a new session record.
- **FR-012**: System MUST support listing all sessions, ordered by date (most recent first).
- **FR-013**: System MUST support filtering sessions by car name.
- **FR-014**: System MUST support retrieving a single session by its unique identifier.

**Recommendations Storage:**

- **FR-015**: System MUST store recommendations linked to a session, each with: unique identifier, session reference, status (pending/accepted/rejected), summary text, and a list of individual parameter changes.
- **FR-016**: Each parameter change within a recommendation MUST include: the setup section, parameter name, old value, new value, and reasoning text.
- **FR-017**: System MUST support saving a new recommendation for a session.
- **FR-018**: System MUST support retrieving all recommendations for a given session.
- **FR-019**: System MUST support updating the status of a recommendation (pending to accepted, or pending to rejected).

**Conversation Storage:**

- **FR-020**: System MUST store messages linked to a session, each with: unique identifier, session reference, role (user or assistant), content text, and timestamp.
- **FR-021**: System MUST support saving a new message for a session.
- **FR-022**: System MUST support retrieving all messages for a session in chronological order.
- **FR-023**: System MUST support deleting all messages for a session (clear conversation).

### Key Entities

- **Configuration**: The user's persistent settings — AC installation path, setups path, LLM provider, LLM model. Stored as a single JSON file. All fields optional with defaults.
- **Session**: A record of one analyzed telemetry session — unique identifier, car, track, date, lap count, best lap time. Linked to recommendations and messages.
- **Recommendation**: A setup change suggestion from the AI engineer — unique identifier, linked session, status (pending/accepted/rejected), summary, and a list of parameter changes.
- **Parameter Change**: A single setup modification within a recommendation — setup section, parameter name, old value, new value, and reasoning.
- **Message**: A single conversation turn between user and AI engineer — unique identifier, linked session, role, content, timestamp.

## Assumptions

- The configuration file location is fixed at `data/config.json` relative to the project root. This is sufficient for a single-user desktop application.
- The storage database location is fixed at `data/ac_engineer.db` relative to the project root.
- Session identifiers come from the upstream parser (e.g., derived from the telemetry filename or metadata) and are unique strings.
- The system is single-user and single-process for typical usage; no multi-user concurrency is required.
- Recommendation parameter changes are stored as structured data (section, parameter, old/new values, reasoning), not free text.
- Message roles are limited to "user" and "assistant" — no system messages need to be persisted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Configuration survives application restart — a setting written before closing the application is readable after reopening, 100% of the time.
- **SC-002**: A missing or corrupted configuration file never causes a crash — the system starts successfully with defaults in all corruption scenarios.
- **SC-003**: Session list returns results ordered by date (most recent first) and filtering by car name returns only matching sessions, verified across at least 10 test sessions.
- **SC-004**: Recommendation status transitions (pending to accepted, pending to rejected) persist correctly and are reflected on subsequent reads.
- **SC-005**: Conversation messages for a session are retrievable in exact chronological order after application restart.
- **SC-006**: Clearing a conversation removes all messages for that session without affecting other sessions' data.
- **SC-007**: All storage operations (save, list, retrieve, update, delete) complete in under 100 milliseconds for datasets up to 1,000 records.
- **SC-008**: All public functions in the config and storage modules are covered by automated tests.
