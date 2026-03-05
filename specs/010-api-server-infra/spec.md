# Feature Specification: API Server Infrastructure

**Feature Branch**: `010-api-server-infra`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Build the base server infrastructure for AC Race Engineer (Phase 6.1)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Desktop App Launches the Server (Priority: P1)

The Tauri desktop app starts the backend server as a subprocess when the application opens. The server boots quickly and signals that it is ready to accept requests. The desktop app confirms connectivity by calling the health check endpoint before rendering the main UI.

**Why this priority**: Without a running server, no other feature can function. This is the absolute foundation — the app cannot communicate with the backend without it.

**Independent Test**: Can be fully tested by starting the server process and verifying the health check responds with a success status and version information.

**Acceptance Scenarios**:

1. **Given** the server is not running, **When** the server process is started with default settings, **Then** the health check endpoint responds successfully within 3 seconds of launch.
2. **Given** the server is running, **When** the health check endpoint is called, **Then** the response includes the system version and a confirmation that the server is operational.
3. **Given** the server is started with a custom port (via argument or environment variable), **When** the health check endpoint is called on that port, **Then** it responds successfully.

---

### User Story 2 - Desktop App Tracks a Long-Running Job (Priority: P1)

The user triggers a long-running operation (such as parsing telemetry or running the AI engineer). The desktop app receives a job identifier, connects to a WebSocket, and displays real-time progress updates. When the job completes, the app shows the result; if it fails, the app shows an error message.

**Why this priority**: Core operations like telemetry parsing and AI analysis take several seconds. Without background job tracking, the UI would freeze or have no way to show progress — making the app unusable for its primary purpose.

**Independent Test**: Can be fully tested by creating a mock job, subscribing to its WebSocket, verifying progress events stream in order, and confirming the final completion or error event arrives.

**Acceptance Scenarios**:

1. **Given** a job has been created and is pending, **When** the client connects to the job's WebSocket, **Then** the client receives progress events as the job advances, each including a percentage and a description of the current step.
2. **Given** a job is running, **When** it completes successfully, **Then** the client receives a completion event containing the job result.
3. **Given** a job is running, **When** it fails, **Then** the client receives an error event containing a description of what went wrong.
4. **Given** a client was disconnected from a job's WebSocket, **When** it reconnects using the same job identifier, **Then** it receives the current status of the job (including the result if the job already finished).

---

### User Story 3 - Desktop App Handles Server Errors Gracefully (Priority: P2)

The user performs an action that results in a server error (invalid request, resource not found, internal failure). The desktop app displays a clear, user-friendly error message derived from the server's uniform error response format.

**Why this priority**: Consistent error handling is essential for a polished user experience, but it is secondary to the server actually running and processing jobs.

**Independent Test**: Can be fully tested by sending invalid requests to the server and verifying that every error response follows the same format with actionable information.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** the client sends a request to a non-existent endpoint, **Then** the response follows the standard error format with a "not found" indication.
2. **Given** the server is running, **When** the client sends a malformed request, **Then** the response follows the standard error format with details about what was wrong.
3. **Given** the server encounters an unexpected internal failure, **Then** the response follows the standard error format without exposing sensitive system internals.

---

### User Story 4 - Desktop App Connects from a Different Port (Priority: P2)

During development, the React UI runs on a separate port from the backend server. The developer's browser makes cross-origin requests to the server, and these requests succeed because the server has CORS configured for localhost origins.

**Why this priority**: CORS is required for the development workflow where the frontend dev server and backend run on different ports. Without it, the browser blocks all API calls during development.

**Independent Test**: Can be fully tested by making a cross-origin request from a different localhost port and verifying the response includes the correct CORS headers.

**Acceptance Scenarios**:

1. **Given** the server is running on one port, **When** a browser on a different localhost port makes a cross-origin request, **Then** the server responds with appropriate CORS headers and the request succeeds.
2. **Given** the server is running, **When** a preflight OPTIONS request is received from a localhost origin, **Then** the server responds with the allowed methods and headers.

---

### Edge Cases

- What happens when the client requests a job that does not exist? The server returns a standard error indicating the job was not found.
- What happens when two clients subscribe to the same job via WebSocket? Both receive the same progress events independently.
- What happens when the server is asked to shut down while jobs are still running? Running jobs are cancelled and the server shuts down cleanly without hanging.
- What happens when the client sends an invalid job_id format in the WebSocket path? The server rejects the connection with a clear error.
- What happens when the job store grows large from many completed jobs? Completed jobs are retained in memory for a reasonable period but can be evicted to prevent unbounded memory growth.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST start an HTTP server that listens on a configurable port (via command-line argument or environment variable), defaulting to a sensible port if none is specified.
- **FR-002**: System MUST expose a health check endpoint that returns the server's operational status and the application version.
- **FR-003**: System MUST configure CORS to allow requests from any localhost origin (any port) during development.
- **FR-004**: System MUST provide a job manager that can create, track, and complete background jobs entirely in memory.
- **FR-005**: Each job MUST have a unique identifier, a status (pending, running, completed, failed), a progress percentage (0-100), an optional description of the current step, and a result or error upon completion.
- **FR-006**: System MUST expose a WebSocket endpoint that accepts a job identifier and streams progress events to the connected client in real time.
- **FR-007**: WebSocket progress events MUST include the job status, progress percentage, and current step description. Completion events MUST include the result. Error events MUST include the error details.
- **FR-008**: If a client connects to a job's WebSocket after the job has already completed or failed, the system MUST immediately send the final status event.
- **FR-009**: All API error responses MUST use a uniform format that includes an error type, a human-readable message, and sufficient context for the UI to display a useful notification.
- **FR-010**: System MUST handle unexpected exceptions with the uniform error format, without exposing internal stack traces or system details to the client.
- **FR-011**: System MUST provide a clean entry point that can be invoked as a subprocess by the desktop shell (Tauri).
- **FR-012**: System MUST shut down cleanly when requested, cancelling any in-progress jobs and closing all WebSocket connections without hanging.

### Key Entities

- **Job**: Represents a background operation. Attributes: unique identifier, type label, status (pending/running/completed/failed), progress (0-100), current step description, result (on completion), error (on failure), creation timestamp.
- **JobEvent**: A message sent over WebSocket to a subscribed client. Contains the event type (progress, completed, error), the current job status snapshot, and the relevant payload (progress data, result, or error details).
- **ErrorResponse**: The uniform error envelope returned by all API error handlers. Contains an error type/code, a human-readable message, and optional detail fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The server responds to the health check endpoint within 3 seconds of process start.
- **SC-002**: A mock job that runs 5 steps completes its full lifecycle (create, progress updates, completion) and the subscribed WebSocket client receives all events in correct order with no dropped messages.
- **SC-003**: 100% of API error responses (not found, bad request, internal error) conform to the uniform error format.
- **SC-004**: Cross-origin requests from any localhost port succeed with correct CORS headers.
- **SC-005**: The server shuts down within 5 seconds of receiving a stop signal, with no orphaned background tasks or hanging connections.
- **SC-006**: All infrastructure components (server, job manager, WebSocket, error handling) are covered by automated tests that verify the complete lifecycle described in the user scenarios.
