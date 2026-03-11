# Feature Specification: Cache Token Tracking

**Feature Branch**: `031-cache-token-tracking`
**Created**: 2026-03-11
**Status**: Draft
**Input**: User description: "Phase 11.1 — Cache Token Tracking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Cache Savings in Usage Details (Priority: P1)

A user runs an engineer analysis or sends a chat message. After the LLM responds, they open the usage detail modal to understand token consumption. They see cache read and cache write token counts per agent alongside the existing input and output token counts. This lets them understand how much of the input was served from the provider's prompt cache (cheaper) versus fresh input (full price).

**Why this priority**: This is the core value — users need per-agent cache breakdown to understand actual costs. Without it, all input tokens appear identically priced, making cost assessment inaccurate.

**Independent Test**: Can be fully tested by triggering an engineer analysis or chat message with a caching-enabled provider, then verifying the usage detail modal shows cache read and cache write per agent.

**Acceptance Scenarios**:

1. **Given** a completed engineer analysis where the provider returned cache usage data, **When** the user opens the usage detail modal, **Then** each agent row shows cache read tokens and cache write tokens alongside input and output tokens.
2. **Given** a completed chat message where the provider returned cache usage data, **When** the user opens the usage detail modal, **Then** the agent row shows cache read and cache write token counts.
3. **Given** a completed interaction where the provider returned zero cache tokens, **When** the user opens the usage detail modal, **Then** no cache information is shown for that agent, and the display looks identical to current behavior.
4. **Given** an older record created before this feature (no cache data stored), **When** the user opens the usage detail modal, **Then** the modal works normally without errors and shows no cache information.

---

### User Story 2 - Cache Totals in Summary Bar (Priority: P2)

A user glances at the usage summary bar on an assistant message (in both analysis recommendations and chat) and wants a quick sense of cache savings without opening the detail modal. The summary bar shows aggregated cache read token count when non-zero.

**Why this priority**: The summary bar provides at-a-glance visibility. It builds on the detail modal (P1) by aggregating the same data, but the detail modal is more critical for accurate cost understanding.

**Independent Test**: Can be tested by rendering the summary bar with usage data containing non-zero cache tokens and verifying the cache count appears.

**Acceptance Scenarios**:

1. **Given** usage data with non-zero total cache read tokens across agents, **When** the summary bar renders, **Then** the cache read total is displayed alongside input and output totals.
2. **Given** usage data where all cache values are zero, **When** the summary bar renders, **Then** no cache information appears and the bar looks identical to current behavior.

---

### Edge Cases

- What happens when a record was created before this feature (no cache columns in the stored data)? The system treats missing values as zero and does not error.
- What happens when a provider does not support caching and returns no cache fields? The system defaults both values to zero and hides cache UI elements.
- What happens when cache_read_tokens is non-zero but cache_write_tokens is zero (or vice versa)? Each field is independent; the UI shows whichever has a non-zero value.
- What happens when the database is upgraded from the old schema? New columns have default values so existing rows remain valid without destructive migration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture cache read token count and cache write token count from every LLM interaction (both engineer analysis and chat) when the agent framework provides these values.
- **FR-002**: System MUST store cache read tokens and cache write tokens as separate fields in each LLM event record, defaulting to 0 when not provided.
- **FR-003**: System MUST add persistent storage fields with a default value of 0 so that existing records created before this feature remain valid without destructive migration.
- **FR-004**: System MUST include cache read tokens and cache write tokens in the recommendation usage response, both in per-agent detail and in aggregated totals.
- **FR-005**: System MUST include cache read tokens and cache write tokens in the message usage response, both in per-agent detail and in aggregated totals.
- **FR-006**: The usage detail modal MUST show cache read and cache write token counts per agent when either value is non-zero for that agent.
- **FR-007**: The usage summary bar MUST show aggregated cache read tokens when the total across all agents is non-zero.
- **FR-008**: The UI MUST NOT show any cache-related information when all cache values are zero (preserving current appearance for older records and non-caching providers).
- **FR-009**: System MUST handle the case where the agent framework returns no cache fields by defaulting both values to 0.

### Key Entities

- **LlmEvent**: An existing entity representing one LLM interaction. Gains two new attributes: cache read token count and cache write token count, both defaulting to zero.
- **UsageTotals**: An existing aggregate entity summarizing token usage across agents. Gains two new attributes: total cache read tokens and total cache write tokens.
- **AgentUsageDetail**: An existing per-agent detail entity. Gains two new attributes: cache read tokens and cache write tokens for that specific agent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of new LLM interactions (analysis and chat) persist cache read and cache write token values; zero values are stored when the provider does not supply cache data.
- **SC-002**: Usage responses include cache token fields for all interactions, with values matching what the agent framework reported.
- **SC-003**: Users can see cache token information in both the summary bar and the detail modal when cache data is present (non-zero).
- **SC-004**: Records created before this feature continue to load and display correctly, with no errors and no spurious cache information shown.
- **SC-005**: All existing tests continue to pass without modification (backward compatibility preserved).

## Assumptions

- The agent framework's usage object already provides cache read and cache write token counts from all three supported providers (Anthropic, OpenAI, Gemini). No framework-level changes are needed.
- Cache read tokens are a subset of input tokens (not additive). The UI should present them as a portion of input that was cached, not as a separate token category.
- Cache write tokens represent the initial caching cost; they are tracked for accuracy but are typically a small number.
- The persistent storage supports adding new fields with default values to existing record structures without destructive migration.
- No changes to tool call detail tracking are needed — cache tracking is at the event level, not at the individual tool call level.
