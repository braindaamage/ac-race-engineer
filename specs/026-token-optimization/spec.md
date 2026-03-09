# Feature Specification: Token Optimization

**Feature Branch**: `026-token-optimization`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Sub-phase 9.4 — Token Optimization for the AI engineer pipeline. Eliminate four inefficiency patterns that cause excessive token consumption."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reduced Token Consumption on Analysis (Priority: P1)

A user triggers an engineer analysis on a session. The system performs the analysis using significantly fewer tokens than before, producing the same quality recommendations. The user notices no difference in the output — the optimization is entirely invisible.

**Why this priority**: This is the core goal. Excessive token usage translates directly to higher cost and slower response times, especially on smaller models. The four optimization patterns combined should dramatically reduce token consumption.

**Independent Test**: Can be verified by running an identical analysis before and after the optimization and comparing token usage (from the usage tracking in phase 9.2) while confirming recommendation output remains equivalent.

**Acceptance Scenarios**:

1. **Given** a session with detected signals, **When** the user requests an engineer analysis, **Then** the system completes the analysis with fewer total tokens than the pre-optimization baseline, and the recommendations are functionally equivalent.
2. **Given** a session analyzed with a smaller model (e.g., Gemini Flash Lite), **When** the analysis completes, **Then** total token consumption is at least 50% lower than the pre-optimization baseline for the same session and model.
3. **Given** any analysis request, **When** the analysis completes, **Then** the user sees no difference in the UI, response format, or recommendation quality compared to the pre-optimization behavior.

---

### User Story 2 - Batch Tool Calls Replace Repetitive Single-Item Calls (Priority: P1)

An agent needing multiple parameter ranges, lap details, or corner metrics retrieves them all in a single tool call instead of making N separate calls. This eliminates N-1 round-trips worth of accumulated message history per batch.

**Why this priority**: The single-item-per-call pattern is the primary driver of message history bloat. Each tool call adds a request-response pair to the conversation, and the full history is re-sent on every subsequent turn. Batching is the highest-impact change.

**Independent Test**: Can be verified by running an analysis and confirming that agents use batch tool calls (accepting lists) and that the returned data matches what the individual calls would have returned.

**Acceptance Scenarios**:

1. **Given** an agent that needs ranges for 4 setup sections, **When** it calls the range tool, **Then** it passes all 4 section names in a single call and receives a dictionary mapping each section to its range data.
2. **Given** an agent that needs metrics for laps 2, 3, and 5, **When** it calls the lap detail tool, **Then** it passes all 3 lap numbers in a single call and receives a dictionary mapping each lap number to its metrics.
3. **Given** an agent that requests a section name that does not exist, **When** the batch tool processes the request, **Then** the response includes the valid results and a "not found" entry for the missing item, without failing the entire batch.

---

### User Story 3 - Knowledge Pre-loaded Into Agent Context (Priority: P1)

When an agent starts reasoning about a domain, it already has the relevant vehicle dynamics knowledge fragments embedded in its initial prompt. It does not need to search for basic domain knowledge during reasoning.

**Why this priority**: Dynamic knowledge search calls return large text fragments that accumulate in the conversation history. Pre-loading the most relevant fragments into the initial prompt avoids these costly mid-conversation expansions.

**Independent Test**: Can be verified by confirming that the agent's initial prompt contains knowledge fragments relevant to its domain signals, and that the agent can reason about vehicle dynamics without calling the search tool.

**Acceptance Scenarios**:

1. **Given** an agent assigned to the "balance" domain with signals "high_understeer" and "brake_balance_issue", **When** the agent's prompt is constructed, **Then** it contains pre-selected knowledge fragments relevant to those signals, up to a maximum of 8 fragments.
2. **Given** a session with no detected signals, **When** the agent's prompt is constructed, **Then** the knowledge context section is empty, and the agent relies on the fallback search tool if it needs knowledge.
3. **Given** the same session data analyzed twice, **When** knowledge fragments are selected for pre-loading, **Then** the exact same fragments are selected in the same order both times (deterministic selection).

---

### User Story 4 - Redundant Tool Removed (Priority: P2)

The get_current_value tool is removed from the agent toolset. Agents that previously called this tool to look up setup parameter values find those values already present in the session data section of their initial prompt, where they have always been included.

**Why this priority**: While each individual call is small, the tool is entirely redundant — the data it returns is already in the prompt. Removing it eliminates wasted turns and simplifies the tool surface.

**Independent Test**: Can be verified by confirming that no agent has access to get_current_value, that the user prompt still contains all setup parameter values, and that recommendation quality is unaffected.

**Acceptance Scenarios**:

1. **Given** an agent built for any domain, **When** inspecting its registered tools, **Then** get_current_value is not among them.
2. **Given** a session with active setup parameters, **When** the user prompt is built, **Then** the "Current Setup Parameters" section contains all parameter values (unchanged from current behavior).
3. **Given** an analysis performed after tool removal, **When** comparing recommendations to a pre-removal baseline on identical session data, **Then** the recommendations are functionally equivalent.

---

### User Story 5 - Agent Execution Turn Limit (Priority: P2)

Each specialist agent has a hard limit on the number of reasoning turns it can take. If an agent hits the limit, it is stopped gracefully, its partial results (if any) are discarded, and the other agents continue unaffected.

**Why this priority**: Without a turn limit, a model prone to over-calling tools can consume tokens indefinitely. The limit acts as a safety net, especially important for smaller or less disciplined models.

**Independent Test**: Can be verified by simulating an agent that would exceed the turn limit and confirming it is stopped, that other agents complete normally, and that the final response is still delivered (minus the stopped agent's contribution).

**Acceptance Scenarios**:

1. **Given** a specialist agent executing an analysis, **When** it reaches the maximum allowed turns, **Then** execution is stopped and the agent's result is excluded from the final response.
2. **Given** one agent hits the turn limit, **When** other agents are still running or pending, **Then** they continue to execute normally and their results are included in the final response.
3. **Given** all agents complete within the turn limit, **When** the analysis finishes, **Then** results are identical to what they would have been without any turn limit (no behavioral change for well-behaved agents).

---

### User Story 6 - Fallback Search Tool With Reduced Scope (Priority: P3)

The knowledge search tool remains registered on each agent as a supplementary fallback. Its maximum results are reduced and its description clarifies that primary knowledge is already in context. Agents can still search if they need knowledge beyond what was pre-loaded.

**Why this priority**: Pre-loading covers the common case, but edge cases may require additional knowledge. Keeping the search tool ensures no regression in coverage, while the reduced result limit and updated description discourage unnecessary use.

**Independent Test**: Can be verified by confirming the search tool is still registered, returns fewer results than before, and has an updated description mentioning pre-loaded knowledge.

**Acceptance Scenarios**:

1. **Given** an agent with pre-loaded knowledge, **When** it calls the search tool, **Then** it receives a reduced number of results (fewer than the current limit of 5).
2. **Given** the search tool's description, **When** an agent reads it, **Then** the description indicates that primary knowledge is already available in context and this tool is for supplementary searches only.

---

### Edge Cases

- What happens when a signal maps to no knowledge fragments? The agent receives an empty knowledge context section and must rely on the fallback search tool.
- What happens when more than 8 fragments are relevant to a domain's signals? Only the first 8 are included, in the deterministic order produced by get_knowledge_for_signals(), and the rest are discoverable via the fallback search tool.
- What happens when a batch tool call requests zero items (empty list)? The tool returns an empty dictionary without error.
- What happens when an agent hits the turn limit on its very first tool call? The agent produces no result, and the final response is assembled from the remaining agents' contributions.
- What happens when all agents hit the turn limit? The system returns a response indicating no recommendations could be generated, without crashing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove the get_current_value tool entirely from the agent toolset. No agent may call it.
- **FR-002**: System MUST replace get_setup_range with a batch version that accepts a list of section names and returns a dictionary mapping each name to its range data (or a "not found" indicator).
- **FR-003**: System MUST replace get_lap_detail with a batch version that accepts a list of lap numbers and returns a dictionary mapping each number to its lap metrics (or a "not found" indicator).
- **FR-004**: System MUST replace get_corner_metrics with a batch version that accepts a list of corner numbers (and an optional lap number) and returns a dictionary mapping each corner number to its metrics (or a "not found" indicator).
- **FR-005**: Batch tools MUST preserve the same data fidelity as their single-item predecessors — same fields, same formatting, same precision.
- **FR-006**: System MUST select and inject relevant knowledge fragments into each agent's initial user prompt before reasoning begins.
- **FR-007**: Knowledge fragment selection MUST be deterministic: identical session data and signals MUST always produce the same fragments in the same order.
- **FR-008**: The maximum number of pre-loaded knowledge fragments per agent MUST be capped at 8.
- **FR-009**: When no signals are detected for a domain, the agent MUST receive an empty knowledge context section.
- **FR-010**: The search_kb tool MUST remain available as a supplementary fallback on all agents.
- **FR-011**: The search_kb tool's maximum results MUST be reduced from the current limit (5) to 2.
- **FR-012**: The search_kb tool's description MUST be updated to state that primary knowledge is already pre-loaded in context and this tool is for supplementary searches only.
- **FR-013**: System MUST enforce a hard turn limit on every specialist agent execution.
- **FR-014**: When an agent exceeds its turn limit, the system MUST stop that agent gracefully and exclude its results from the final response.
- **FR-015**: Per-agent error isolation MUST ensure that one agent hitting the turn limit does not block or cancel other agents.
- **FR-016**: All optimizations MUST be invisible to the user. No UI changes, no user-facing messages about optimization.
- **FR-017**: All existing tests MUST continue to pass. Affected tests MUST be updated to reflect the new batch tool signatures and removed tool.

### Key Entities

- **KnowledgeFragment**: A unit of vehicle dynamics knowledge (source file, section title, content, tags) selected for pre-loading into agent context.
- **AgentDeps**: The dependency object passed to agent tools, containing session summary, parameter ranges, domain signals, knowledge fragments, and resolution tier.
- **SessionSummary**: The pre-computed session data that includes active setup parameters (the data that makes get_current_value redundant).
- **SpecialistResult**: The output of each domain agent, containing proposed setup changes and explanations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total token consumption per analysis is reduced by at least 50% compared to the pre-optimization baseline, measured on the same session data and model.
- **SC-002**: The number of tool calls per agent is reduced — agents needing N items of the same type make 1 batch call instead of N individual calls.
- **SC-003**: Zero calls to get_current_value occur in any analysis (the tool no longer exists).
- **SC-004**: Knowledge fragment pre-loading is deterministic: running the same analysis twice produces identical fragment selections.
- **SC-005**: No agent exceeds the configured turn limit under any circumstances.
- **SC-006**: All existing tests pass after the changes, with affected tests updated to match new signatures.
- **SC-007**: Recommendation quality is preserved: analyses on identical sessions produce functionally equivalent recommendations before and after optimization.
- **SC-008**: The user experience is unchanged — no visible differences in the UI, response format, or interaction flow.
