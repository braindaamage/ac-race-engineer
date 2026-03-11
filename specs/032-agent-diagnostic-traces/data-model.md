# Data Model: Agent Diagnostic Traces

**Feature**: 032-agent-diagnostic-traces | **Date**: 2026-03-11

## Entity Changes

### ACConfig (modified)

Configuration model in `backend/ac_engineer/config/models.py`.

**New field**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `diagnostic_mode` | `bool` | `False` | When true, agent conversation traces are captured to disk |

**Existing fields** (unchanged): `ac_install_path`, `setups_path`, `llm_provider`, `llm_model`, `ui_theme`, `api_key`, `onboarding_completed`

**Serialization**: Add `"diagnostic_mode": self.diagnostic_mode` to the `_serialize()` method.

### No Database Changes

Traces are stored as files on disk, not in the database. No migration needed.

## New Entities

### AgentTrace (in-memory, not persisted to DB)

Intermediate data structure used during trace serialization. Represents one agent's complete conversation.

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `str` | Agent domain name (e.g., "balance", "tyre", "principal") |
| `system_prompt` | `str` | The system prompt the agent received |
| `user_prompt` | `str` | The user prompt sent to the agent |
| `messages` | `list[dict]` | Serialized conversation turns (see Message Turn below) |
| `structured_output` | `dict \| None` | The agent's final structured result (SpecialistResult for analysis, None for chat) |

### Message Turn (dict structure within AgentTrace.messages)

Each turn in the conversation is a dict with:

| Key | Type | Description |
|-----|------|-------------|
| `role` | `str` | `"assistant"`, `"tool_call"`, or `"tool_response"` |
| `content` | `str` | Text content (for assistant) or JSON-formatted parameters/response |
| `tool_name` | `str \| None` | Tool name (for tool_call and tool_response turns) |
| `tool_call_id` | `str \| None` | Correlating ID for tool call/response pairs |

### TraceFile (Markdown file on disk)

Physical file stored at `data/traces/{type}_{id}.md`.

**Naming convention**:
- Analysis traces: `rec_{recommendation_id}.md`
- Chat traces: `msg_{message_id}.md`

**File structure** (Markdown format):

```markdown
# Diagnostic Trace: {type}

**ID**: {recommendation_id or message_id}
**Session**: {session_id}
**Timestamp**: {ISO 8601}
**Agents**: {comma-separated domain list}

---

## Agent: {domain}

### System Prompt

{system prompt text}

### User Prompt

{user prompt text}

### Conversation

#### Assistant

{assistant text}

#### Tool Call: {tool_name}

```json
{tool call parameters}
```

#### Tool Response: {tool_name}

```json
{tool response content}
```

#### Assistant

{next assistant text}

### Structured Output

```json
{final structured result as JSON}
```

---

## Agent: {next domain}

{same structure repeats}
```

## API Response Types

### TraceResponse (new)

API serializer for trace endpoint responses.

| Field | Type | Description |
|-------|------|-------------|
| `available` | `bool` | Whether a trace exists for this ID |
| `content` | `str \| None` | The full Markdown trace content (null if not available) |
| `trace_type` | `str` | `"recommendation"` or `"message"` |
| `id` | `str` | The recommendation_id or message_id |

### Frontend Type: TraceResponse (TypeScript)

```typescript
export interface TraceResponse {
  available: boolean;
  content: string | null;
  trace_type: "recommendation" | "message";
  id: string;
}
```

## Data Flow

```
diagnostic_mode == true
         │
   agent.run() completes
         │
   result.all_messages() ──► serialize_agent_trace()
         │                         │
         │                    AgentTrace dict
         │                         │
   (repeat for each specialist)    │
         │                         │
   recommendation persisted ──► write_trace()
         │                         │
         │                  data/traces/rec_{id}.md
         │
         ▼
   GET /recommendations/{id}/trace
         │
   read trace file ──► TraceResponse { available: true, content: "..." }
         │
         ▼
   Frontend TraceModal renders Markdown content
```

## Config Flow

```
Settings UI toggle ──► PATCH /config { diagnostic_mode: true }
                              │
                    update_config() ──► config.json
                              │
              make_engineer_job() reads config.diagnostic_mode
                              │
                     if true: capture traces
                     if false: skip entirely (zero overhead)
```
