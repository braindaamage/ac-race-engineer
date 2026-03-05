# API Integration Contracts: Desktop App ↔ Backend

**Branch**: `015-desktop-scaffold` | **Date**: 2026-03-05

The desktop app communicates with the backend exclusively via HTTP (`http://127.0.0.1:57832`) and WebSocket (`ws://127.0.0.1:57832`). This document defines the contracts the frontend depends on.

## Existing Endpoints (Phase 6)

### GET /health

Used for sidecar readiness polling during startup.

**Request**: None
**Response** (200):
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Frontend usage**: Polled at 500ms intervals (max 30 retries) during splash screen. Transition to main UI when `status === "ok"`.

---

### GET /config

Used to rehydrate theme preference on app launch.

**Request**: None
**Response** (200):
```json
{
  "ac_install_path": "",
  "setups_path": "",
  "llm_provider": "anthropic",
  "llm_model": "",
  "ui_theme": "dark"
}
```

**Frontend usage**: Called once after backend ready. Theme is applied before rendering the main UI.

---

### PATCH /config

Used to persist theme preference when user switches themes.

**Request**:
```json
{
  "ui_theme": "light"
}
```

**Response** (200):
```json
{
  "ac_install_path": "",
  "setups_path": "",
  "llm_provider": "anthropic",
  "llm_model": "",
  "ui_theme": "light"
}
```

**Frontend usage**: Fire-and-forget on theme change. If it fails, the theme still applies in-memory; a warning notification is shown.

---

### WebSocket /ws/jobs/{job_id}

Used for real-time job progress tracking.

**Connection**: `ws://127.0.0.1:57832/ws/jobs/{jobId}`

**Server messages** (JSON):
```json
{
  "event": "progress",
  "job_id": "abc-123",
  "status": "running",
  "progress": 45,
  "current_step": "Analyzing corners",
  "result": null,
  "error": null
}
```

```json
{
  "event": "completed",
  "job_id": "abc-123",
  "status": "completed",
  "progress": 100,
  "current_step": null,
  "result": { "session_id": "..." },
  "error": null
}
```

```json
{
  "event": "error",
  "job_id": "abc-123",
  "status": "failed",
  "progress": 50,
  "current_step": null,
  "result": null,
  "error": "Analysis failed: insufficient data"
}
```

**Frontend usage**: Open connection per job. Update Zustand `jobProgress` on each message. On `completed`/`error`, trigger toast notification and close connection.

---

## New Endpoints (to be added in this phase)

### POST /shutdown

Triggers graceful server shutdown. Called by the frontend before killing the sidecar process on app exit.

**Request**: None
**Response** (200):
```json
{
  "status": "shutting_down"
}
```

**Frontend usage**: Called in the window `onCloseRequested` handler. Wait up to 2 seconds for response, then kill sidecar regardless.

---

## Component Contracts

### Design System Components

All components in `components/ui/` follow these contracts:

**Button**:
- Props: `variant` ("primary" | "secondary" | "ghost"), `size` ("sm" | "md" | "lg"), `disabled`, `onClick`, `children`
- Primary: brand red background, white text
- Secondary: transparent background, border, text-primary color
- Ghost: transparent, no border, text-secondary color

**Card**:
- Props: `variant` ("default" | "ai"), `children`, `title?`, `padding?`
- Default: surface background, standard border
- AI: surface background, cyan/blue left border accent (3-4px)

**Badge**:
- Props: `variant` ("info" | "success" | "warning" | "error" | "neutral"), `children`
- Each variant uses its semantic color for background/text

**DataCell**:
- Props: `value` (string | number), `delta?` (number), `unit?` (string), `align?` ("left" | "right")
- Always renders value in JetBrains Mono
- Positive delta: green, Negative delta: amber, Zero/none: neutral

**ProgressBar**:
- Props: `value` (0-100), `variant?` ("default" | "success" | "error")
- Animated fill transition

**Tooltip**:
- Props: `content` (string), `position?` ("top" | "bottom" | "left" | "right"), `children`
- Shows on hover with short delay

**Skeleton**:
- Props: `width?`, `height?`, `variant?` ("text" | "circle" | "rect")
- Animated shimmer effect

**EmptyState**:
- Props: `icon` (component), `title` (string), `description` (string), `action?` ({ label, onClick })
- Centered layout with icon, text, optional action button

**Toast**:
- Props: `notification` (Notification object)
- Positioned bottom-right, stacked
- Auto-dismiss timer for non-error types

**Modal**:
- Props: `open` (boolean), `onClose`, `title`, `children`, `actions?` ({ confirm, cancel })
- Backdrop overlay, centered dialog, focus trap
