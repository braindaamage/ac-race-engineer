# Data Model: Desktop App Scaffolding

**Branch**: `015-desktop-scaffold` | **Date**: 2026-03-05

## Entities

### Theme

Represents the active visual theme applied to the entire application.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | `"dark"` or `"light"` | Theme identifier |
| label | string | non-empty | Display name ("Night Grid" or "Garage Floor") |

**State transitions**: None — themes are static definitions. The active theme is a UI state selection.

**Persistence**: The selected theme ID is stored in the backend config as `ui_theme` (default: `"dark"`).

---

### NavigationSection

Represents a section in the sidebar navigation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | unique, one of 5 fixed values | Section identifier (sessions, analysis, compare, engineer, settings) |
| label | string | non-empty | Display label shown in sidebar |
| icon | component | required | Icon component rendered in sidebar |
| path | string | valid route path | URL path for routing |
| requiresSession | boolean | required | Whether this section needs an active session to show content |

**Fixed values** (not user-configurable):
- `sessions` — "Sessions" — `/sessions` — requiresSession: false
- `analysis` — "Lap Analysis" — `/analysis` — requiresSession: true
- `compare` — "Setup Compare" — `/compare` — requiresSession: true
- `engineer` — "Engineer" — `/engineer` — requiresSession: true
- `settings` — "Settings" — `/settings` — requiresSession: false

---

### Notification

Represents a toast notification in the notification system.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | unique, auto-generated | Notification identifier |
| type | enum | `info`, `success`, `warning`, `error` | Visual style and behavior |
| message | string | non-empty | Notification text |
| autoDismiss | boolean | derived from type | true for info/success/warning, false for error |
| duration | number | milliseconds | Auto-dismiss delay (5000ms for non-error) |
| createdAt | timestamp | auto-set | When notification was created |

**State transitions**: Created → Visible → Dismissed (auto or manual)

---

### JobProgress

Tracks the progress of a backend background job via WebSocket.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| jobId | string | non-empty | Backend job identifier |
| status | enum | `pending`, `running`, `completed`, `failed` | Current job state |
| progress | number | 0-100 | Completion percentage |
| currentStep | string or null | optional | Description of current step |
| result | object or null | only when completed | Job result data |
| error | string or null | only when failed | Error message |

**State transitions**: pending → running → completed|failed

---

### Zustand Stores (5 independent stores)

Global UI state managed by Zustand v5. Multiple small stores for independent concerns, each with scoped subscriptions.

#### UIStore (`uiStore.ts`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| activeSection | string | `"sessions"` | Currently active navigation section ID |
| sidebarCollapsed | boolean | `false` | Whether sidebar is in icon-only mode |

**Actions**: `setActiveSection(id)`, `toggleSidebar()`

#### SessionStore (`sessionStore.ts`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| selectedSessionId | string or null | `null` | Currently selected session ID |

**Actions**: `selectSession(id)`, `clearSession()`

#### ThemeStore (`themeStore.ts`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| theme | string | `"dark"` | Active theme ID |

**Actions**: `setTheme(id)` — updates `document.documentElement.dataset.theme` + fires `PATCH /config`

#### NotificationStore (`notificationStore.ts`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| notifications | Notification[] | `[]` | Active notification stack |

**Actions**: `addNotification(type, message)` → returns id, `removeNotification(id)`

#### JobStore (`jobStore.ts`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| jobProgress | Map<string, JobProgress> | `{}` | Active job progress tracking |

**Actions**: `updateJobProgress(jobId, update)`, `removeJob(jobId)`

---

### ACConfig (backend — extended)

The existing `ACConfig` model extended with `ui_theme`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| ac_install_path | Path or null | null | AC installation directory |
| setups_path | Path or null | null | Setups directory |
| llm_provider | string | "anthropic" | LLM provider name |
| llm_model | string or null | null | LLM model override |
| **ui_theme** | **string** | **"dark"** | **UI theme preference (new)** |

**Validation**: `ui_theme` must be one of `"dark"`, `"light"`. Invalid values default to `"dark"`.
