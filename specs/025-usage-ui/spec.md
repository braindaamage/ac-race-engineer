# Feature Specification: Usage UI

**Feature Branch**: `025-usage-ui`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Sub-phase 9.3 — Usage UI. Add token usage summary bar and detail modal to the existing RecommendationCard component in the frontend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Glance at Usage Summary (Priority: P1)

After the AI engineer produces a recommendation, the user wants to quickly see how much AI processing was involved — how many agents ran, how many tokens were consumed, and how many tool calls were made — without leaving the recommendation card.

**Why this priority**: This is the core value of the feature. Without the inline summary, the user has no visibility into usage at all. It also serves as the entry point to the detail modal (P2).

**Independent Test**: Can be fully tested by generating a recommendation with usage data and verifying the summary bar appears at the bottom of the card with the correct aggregated numbers.

**Acceptance Scenarios**:

1. **Given** a recommendation card with associated usage data, **When** the card is rendered, **Then** a summary bar appears at the bottom showing agent count, total input tokens, total output tokens, total tool calls, and a details button.
2. **Given** a recommendation card with no associated usage data, **When** the card is rendered, **Then** no summary bar is shown and no extra vertical space is consumed.
3. **Given** usage data with large token counts (e.g. 847,300 input tokens), **When** the summary bar is rendered, **Then** the number displays as "847.3K" using the compact formatting rules.

---

### User Story 2 - View Detailed Agent Breakdown (Priority: P2)

The user wants to drill into the full breakdown of which agents participated, how many tokens each consumed, how long each took, and what tools each agent called. This helps the user understand the analysis depth and cost distribution across specialist agents.

**Why this priority**: Provides the detailed view that power users and cost-conscious users need. Depends on P1 for the entry point (details button).

**Independent Test**: Can be fully tested by clicking the details button on a recommendation with multi-agent usage data and verifying the modal displays correct per-agent rows with all metrics.

**Acceptance Scenarios**:

1. **Given** a recommendation with usage data for 3 agents, **When** the user clicks the details button on the summary bar, **Then** a modal opens showing a totals row at the top and 3 agent rows below it.
2. **Given** the detail modal is open, **When** the user views an agent row, **Then** they see the agent domain name, input tokens, output tokens, turn count, duration in seconds, and the list of tools called with their token counts.
3. **Given** the detail modal is open, **When** the user presses Escape or clicks outside the modal, **Then** the modal closes.
4. **Given** a recommendation with a single agent, **When** the detail modal opens, **Then** the totals row and the single agent row are both shown (totals row is always present).

---

### Edge Cases

- What happens when the usage endpoint returns zero tokens for all agents? The summary bar still renders (since usage data exists), showing all zeros.
- What happens when an agent has zero tool calls? The tool calls section for that agent row is empty or omitted in the detail modal.
- What happens when the usage fetch fails (network error)? The summary bar is not rendered, matching the "no usage data" behavior. No error is shown to the user since usage is supplementary information.
- What happens when token counts are exactly at formatting boundaries (999, 1000, 999999, 1000000)? The formatting function correctly transitions between raw, K-suffix, and M-suffix representations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an inline usage summary bar at the bottom of each recommendation card when usage data is available for that recommendation.
- **FR-002**: The summary bar MUST show: agent count, total input tokens, total output tokens, total tool calls, and a button to open the detail view.
- **FR-003**: The summary bar MUST NOT render when no usage data exists for the recommendation (no empty state, no placeholder, no extra whitespace).
- **FR-004**: System MUST open a detail modal when the user clicks the details button on the summary bar.
- **FR-005**: The detail modal MUST display a totals row showing aggregated input tokens, output tokens, total tool calls, and total agent count.
- **FR-006**: The detail modal MUST display one row per agent showing: domain name, input tokens, output tokens, turn count, duration in seconds, and tool calls with per-tool token counts.
- **FR-007**: Token numbers MUST be formatted using compact notation: values under 1,000 display as-is, values 1,000–999,999 display with K suffix and one decimal (e.g. 847.3K), values 1,000,000+ display with M suffix and one decimal (e.g. 1.4M).
- **FR-008**: All numeric data (token counts, durations) MUST render in the monospace font (JetBrains Mono), consistent with numeric data elsewhere in the app.
- **FR-009**: The detail modal MUST use the existing Modal component from the design system.
- **FR-010**: All colors MUST come from the existing CSS design tokens. No hardcoded color values.
- **FR-011**: The summary bar MUST be visually secondary to the recommendation content — it must not compete with setup changes or driver feedback sections for visual attention.
- **FR-012**: Usage data MUST be fetched from the existing backend endpoint and treated as immutable once fetched (cached indefinitely for a given recommendation).
- **FR-013**: Duration values in the detail modal MUST display in seconds with one decimal place (e.g. "2.3s").
- **FR-014**: System MUST NOT display any cost calculation or USD amounts. Token counts only.

### Key Entities

- **UsageTotals**: Aggregated usage across all agents for a recommendation — input tokens, output tokens, total tokens, tool call count, agent count.
- **AgentUsageDetail**: Per-agent breakdown — domain (balance/tyre/aero/technique), model name, input tokens, output tokens, tool call count, turn count, duration in milliseconds, list of tool calls.
- **ToolCallInfo**: Individual tool call record — tool name, token count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see AI usage summary on every recommendation that has usage data, without any additional clicks or navigation.
- **SC-002**: Users can access the full agent-by-agent breakdown in two clicks or fewer (one to open details).
- **SC-003**: Token numbers are human-readable at a glance — no raw numbers above 999 are shown without compact formatting.
- **SC-004**: The usage summary does not increase the visual weight of the recommendation card — it remains secondary to the recommendation content.
- **SC-005**: All existing recommendation card functionality (viewing changes, applying recommendations, driver feedback) continues to work unchanged.
- **SC-006**: The usage detail modal follows the same interaction patterns as other modals in the app (keyboard dismiss, backdrop click).

## Assumptions

- The backend endpoint `GET /sessions/{session_id}/recommendations/{recommendation_id}/usage` is already implemented and returns the data shape described in sub-phase 9.2 (UsageTotals + list of AgentUsageDetail).
- The existing Modal component supports a title, scrollable body content, and close behavior (Escape key, backdrop click).
- Agent domains are limited to the four known values: balance, tyre, aero, technique. Domain names are displayed as-is (lowercase).
- Duration comes from the backend in milliseconds and must be converted to seconds for display.
- The formatting function for compact token numbers uses standard rounding (e.g. 1,450 becomes "1.5K", 1,440 becomes "1.4K").
- Trailing zeros after the decimal are preserved for consistency (e.g. 1,000 displays as "1.0K", not "1K").
