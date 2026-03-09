# Research: Usage UI

**Branch**: `025-usage-ui` | **Date**: 2026-03-09

## R1: Token Number Formatting Strategy

**Decision**: Pure utility function `formatTokenCount(n: number): string` with three tiers: raw (<1,000), K suffix (1,000–999,999), M suffix (1,000,000+). One decimal place always shown for K and M.

**Rationale**: The spec requires compact notation with specific thresholds and one-decimal formatting. A standalone pure function is trivially testable and reusable. No external formatting library needed — the logic is ~10 lines.

**Alternatives considered**:
- `Intl.NumberFormat` with `notation: "compact"`: Locale-dependent output (could show "mil" in Spanish locale), and doesn't guarantee the exact format specified (e.g. trailing zero preservation). Rejected for inconsistent output.
- Inline formatting in components: Rejected for code duplication and untestability.

## R2: Hook Architecture — Separate vs. Combined

**Decision**: Add `useRecommendationUsage(sessionId, recommendationId)` as an export from the existing `useRecommendations.ts` hook file, following the same pattern as `useRecommendationDetail`.

**Rationale**: The existing file already exports two hooks (`useRecommendations`, `useRecommendationDetail`). Adding a third usage hook to the same file maintains cohesion — all recommendation-related data fetching lives together. The hook uses `staleTime: Infinity` since usage data is immutable.

**Alternatives considered**:
- Separate `useRecommendationUsage.ts` file: Viable, but breaks the existing convention where recommendation hooks are co-located. A separate file would be warranted only if the hook grew complex.
- Fetching inside RecommendationCard directly: Rejected — violates the pattern of hooks living in `hooks/` and being testable independently.

## R3: Component Decomposition — Summary Bar and Detail Modal

**Decision**: Two new components: `UsageSummaryBar` (rendered inline in RecommendationCard) and `UsageDetailModal` (rendered via Modal from design system). Both live in `frontend/src/views/engineer/`.

**Rationale**: The summary bar is tightly coupled to RecommendationCard layout. The detail modal follows the same pattern as `ApplyConfirmModal` — a view-level component in `views/engineer/` that wraps the shared Modal. Keeping both in the engineer view directory matches existing conventions.

**Alternatives considered**:
- Single component handling both bar and modal: Rejected — conflates two distinct UI responsibilities (inline display vs. overlay).
- Moving modal to `components/ui/`: Rejected — it's feature-specific, not a reusable design system component. `ApplyConfirmModal` follows the same pattern and lives in `views/engineer/`.

## R4: Data Flow — Where Usage is Fetched

**Decision**: Usage data is fetched in `EngineerView` (index.tsx) and passed as a prop to `RecommendationCard`, which passes it down to `UsageSummaryBar`. The detail modal state (open/close) is managed locally in `RecommendationCard` via `useState`.

**Rationale**: EngineerView already orchestrates data fetching for recommendation details via `useQueries`. Adding usage fetching at the same level keeps the data flow consistent. However, unlike apply-modal state (which EngineerView manages because it triggers mutations), the usage modal is read-only — so its open/close state can be local to RecommendationCard, keeping EngineerView simpler.

**Alternatives considered**:
- Fetching inside RecommendationCard: Would work since usage is read-only, but breaks the established pattern where EngineerView owns all data fetching.
- Managing modal state in EngineerView: Rejected — unnecessary complexity for a read-only modal. The apply modal needs EngineerView-level state because applying triggers API mutations and query invalidation. Usage modal has no side effects.

## R5: CSS Approach for Visual Hierarchy

**Decision**: Summary bar uses `--text-muted` color, `--font-size-xs` size, top border separator with `--border` token, and minimal padding. No background color differentiation — just text weight and color to signal secondary importance.

**Rationale**: The spec requires the summary bar to be "visually secondary" to recommendation content. Using muted text and extra-small font size creates sufficient visual hierarchy without adding visual noise. The existing card already uses `--font-size-xs` for setup change values, so the summary bar at the same or smaller size naturally recedes.

**Alternatives considered**:
- Distinct background color for summary bar: Rejected — adds visual weight and competes with card content.
- Collapsible/expandable summary: Rejected — over-engineering for a one-line bar.

## R6: Duration Display Conversion

**Decision**: Convert `duration_ms` (integer from backend) to seconds with one decimal place: `(duration_ms / 1000).toFixed(1)` + "s" suffix.

**Rationale**: The spec requires "duration in seconds with one decimal place (e.g. 2.3s)". The backend stores duration in milliseconds. Simple division and `.toFixed(1)` gives the required format.

**Alternatives considered**: None — the approach is straightforward and matches the spec exactly.
