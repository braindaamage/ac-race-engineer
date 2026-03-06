# Research: Setup Compare View

**Feature**: 019-setup-compare-view
**Date**: 2026-03-06

## No NEEDS CLARIFICATION Items

The technical context has no unknowns. All decisions are informed by existing codebase patterns (Phases 7.1-7.4) and the user's explicit design direction.

## Decision Log

### D1: Stint Selection State Management

**Decision**: Local `useState<[number, number | null]>` tuple for the two selected stint indices.
**Rationale**: Stint selection is component-local, ephemeral, and has no cross-view consumers. Per constitution Principle XII, `useState` is the correct layer for component-local state. Default to the first two stints on load if the session has 2+ stints. Replacing the oldest selection on new pick mirrors the established pattern from AnalysisView's `selectedLaps` state.
**Alternatives considered**: Zustand store (overkill — no other view needs this state), URL params (no router in this app).

### D2: Data Fetching Strategy

**Decision**: Two TanStack Query hooks — `useStints(sessionId)` and `useStintComparison(sessionId, stintA, stintB)`. Both use `staleTime: Infinity`.
**Rationale**: Stints and comparisons are immutable once a session is analyzed. This matches the `useLaps` / `useLapDetail` pattern from Phase 7.4. The comparison hook is `enabled` only when both stint indices are non-null, preventing unnecessary requests. Query key includes `[session_id, stint_a, stint_b]` to cache each pair independently.
**Alternatives considered**: Single hook fetching both (would couple stint list loading with comparison loading, worse UX).

### D3: Setup Diff Grouping

**Decision**: Group `SetupParameterDelta[]` by the `section` field into collapsible sections. Each section header shows the INI section name. Within each section, parameters are listed as rows with old value, arrow, new value.
**Rationale**: The `section` field on `SetupParameterDelta` maps directly to INI file sections (e.g., `[SUSPENSION]`, `[TYRES]`). Grouping by section matches how drivers think about setup categories. Collapsible groups keep the UI focused.
**Alternatives considered**: Flat list (loses organizational context), custom category mapping (violates car-agnostic principle).

### D4: Delta Direction and Color Coding

**Decision**: For numeric deltas, show `+` prefix for increases and `-` for decreases. Color coding: green for improvements (lower lap time, lower tyre temp delta), red for degradations. For setup parameter changes, use up/down arrows (unicode) for numeric values, no arrow for string values.
**Rationale**: Sign + color is the most intuitive representation for racing drivers. The "improvement" direction varies by metric — lower lap time is better, but higher peak lateral G is better. This logic lives in a utility function.
**Alternatives considered**: Color only (harder to parse at a glance), always green=increase (misleading — increase isn't always good).

### D5: Empty State Handling

**Decision**: Four distinct empty states handled via early returns in CompareView, following the exact pattern from AnalysisView:
1. No session selected → EmptyState with "Go to Sessions" action
2. Session not analyzed → EmptyState explaining analysis is required
3. Single stint → EmptyState explaining comparison needs 2+ stints
4. Loading → Skeleton placeholders

**Rationale**: Direct replication of the AnalysisView pattern ensures visual consistency and follows established conventions.
**Alternatives considered**: Single generic empty state (less informative).

### D6: Toggle for Unchanged Parameters

**Decision**: A local `useState<boolean>` toggle ("Show all parameters") in the SetupDiff component. When off (default), only parameters in the `setup_changes` array are shown. When on, the view needs all parameters from both stints — but the current `StintComparison` API only returns changed parameters.
**Rationale**: The backend `GET /sessions/{id}/compare` endpoint returns only `setup_changes` (changed parameters) and `metric_deltas`. To show all parameters, we would need to fetch the full setup for each stint, which is not currently exposed as an API endpoint. Therefore, the "show all" toggle will only be implemented if the backend provides the data. For the initial implementation, the toggle will be omitted and documented as a future enhancement if/when a full setup endpoint is added.
**Resolution**: The toggle is descoped from P3 to a future enhancement. The UI will show changed parameters only (which is the default and most useful behavior). The spec's FR-005 is satisfied by the fact that only changed parameters are shown — the toggle for "all" requires additional backend support.

### D7: Mismatched Parameter Sets

**Decision**: Parameters present in only one stint's `setup_changes` will already appear in the API response with a value in one side and potentially a different type marker. In the UI, if `value_a` or `value_b` is not a number (e.g., could be an empty string or a special marker), display "—" for the missing side.
**Rationale**: The `SetupParameterDelta` model has `value_a: float | str` and `value_b: float | str`. The backend already handles producing the delta list. The frontend just needs to render whatever values come through, using "—" as a fallback for any missing/empty values.
