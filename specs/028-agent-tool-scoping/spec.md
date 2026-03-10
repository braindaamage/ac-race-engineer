# Feature Specification: Agent Tool Scoping

**Feature Branch**: `028-agent-tool-scoping`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Restrict each specialist AI agent to only the tools relevant to its domain, matching the tool sets documented in each agent's skill prompt."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Domain-Restricted Tool Access (Priority: P1)

When the system runs specialist agents to analyze a race session, each agent only has access to the tools that are relevant to its domain. For example, the technique coaching agent (which analyzes driving behavior, not setup parameters) cannot call `get_setup_range`, because that tool is not part of its role. This prevents wasted LLM conversation turns, irrelevant context accumulation, and unnecessary token consumption.

**Why this priority**: This is the core problem. Agents calling irrelevant tools is the direct cause of the token bloat (technique agent went from 21K to 37K input tokens due to two unexpected `get_setup_range` calls).

**Independent Test**: Can be fully tested by building each specialist agent and verifying that only its documented tools are registered. Delivers immediate token savings and correct agent behavior.

**Acceptance Scenarios**:

1. **Given** the technique agent is built, **When** its registered tools are inspected, **Then** only `get_lap_detail`, `get_corner_metrics`, and `search_kb` are available — `get_setup_range` is not registered.
2. **Given** the balance agent is built, **When** its registered tools are inspected, **Then** only `get_setup_range`, `get_corner_metrics`, and `search_kb` are available — `get_lap_detail` is not registered.
3. **Given** the tyre agent is built, **When** its registered tools are inspected, **Then** only `get_setup_range`, `get_lap_detail`, and `search_kb` are available — `get_corner_metrics` is not registered.
4. **Given** the aero agent is built, **When** its registered tools are inspected, **Then** only `get_setup_range`, `get_corner_metrics`, and `search_kb` are available — `get_lap_detail` is not registered.

---

### User Story 2 - Auditable Tool-to-Agent Mapping (Priority: P2)

A developer or auditor can determine which tools each agent has access to by reading a single, explicit mapping in the source code — without running the code or tracing through multiple files. The mapping is a readable data structure, not scattered logic.

**Why this priority**: Auditability is the user's second stated requirement. The mapping should be "explicit and readable" so that changes to tool assignments are easy to review and reason about.

**Independent Test**: Can be verified by reading the source code and confirming that a single, centralized mapping declares the tool set for each domain. The mapping must agree with the skill prompt documents.

**Acceptance Scenarios**:

1. **Given** the agent orchestration source code, **When** a developer reads the tool mapping, **Then** they can see — in one place — which tools each domain (balance, tyre, aero, technique) receives.
2. **Given** the tool mapping, **When** compared to each skill prompt document's listed tools, **Then** they match exactly.

---

### User Story 3 - Principal Agent Tool Access (Priority: P3)

The principal (orchestrator) agent, which verifies and combines specialist results, has its own restricted tool set matching its documented role: only `get_lap_detail` and `get_corner_metrics` for verification purposes.

**Why this priority**: The principal agent also has a skill document with specific tool expectations. Consistency requires it to follow the same scoping pattern, though its impact is lower since it runs once (not per-domain).

**Independent Test**: Can be tested by building the principal agent and verifying only `get_lap_detail` and `get_corner_metrics` are registered.

**Acceptance Scenarios**:

1. **Given** the principal agent is built, **When** its registered tools are inspected, **Then** only `get_lap_detail` and `get_corner_metrics` are available — `search_kb` and `get_setup_range` are not registered.

---

### Edge Cases

- What happens when a new tool is added in the future? The mapping must be updated explicitly — no tool is available to any agent by default.
- What happens when a new specialist domain is added? The system should fail clearly if no tool mapping is defined for that domain, rather than silently assigning all tools or no tools.
- What happens if the tool mapping references a tool function that doesn't exist? This should be caught at agent build time, not at runtime during a session analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define an explicit, centralized mapping from each agent domain to its permitted tool set.
- **FR-002**: When building a specialist agent, the system MUST register only the tools listed in the mapping for that domain — no others.
- **FR-003**: The tool mapping MUST match the tools documented in each domain's skill prompt file (balance.md, tyre.md, aero.md, technique.md, principal.md).
- **FR-004**: The mapping MUST be a readable data structure that can be audited by reading the source code without executing it.
- **FR-005**: If a domain is requested that has no entry in the tool mapping, the system MUST fail with a clear error rather than defaulting to all tools or no tools.
- **FR-006**: The tool scoping MUST apply equally to all agent types: specialist agents and the principal agent.

### Key Entities

- **Tool Mapping**: A data structure that associates each agent domain name (string) with a list of tool functions. Centralized in one location, referenced by the agent factory.
- **Agent Domain**: One of: "balance", "tyre", "aero", "technique", "principal". Each domain has exactly one skill prompt and one tool set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each specialist agent has access to exactly the tools documented in its skill prompt — no more, no fewer. Verifiable by inspecting the agent's registered tool list after construction.
- **SC-002**: The technique agent no longer calls `get_setup_range` during session analysis, eliminating the extra conversation turns and token overhead observed after Phase 9.5.
- **SC-003**: The tool-to-agent mapping is readable in a single location in the source code without executing the program.
- **SC-004**: All existing tests continue to pass with no regressions — the change is internal to agent construction and does not alter tool behavior or analysis output.

## Assumptions

- The 5 skill prompt documents (balance.md, tyre.md, aero.md, technique.md, principal.md) are the authoritative source for which tools each agent should use. The mapping should reflect their current contents.
- The tool implementations themselves do not change — only which agents receive which tools.
- The principal agent is built through a separate code path but should follow the same scoping pattern for consistency.
