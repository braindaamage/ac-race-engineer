# Research: Session Views Visual Polish

**Branch**: `037-session-views-visual-polish` | **Date**: 2026-03-15

## R1: Session Detail Header Data Source Strategy

**Decision**: Use `useSessions()` to find the session record by ID (already fetched by parent views), then use `useCarTracks(car)` from Phase 14.2 to resolve display names, badge URLs, and preview URLs. The header component lives in SessionLayout and receives session data via the existing sessions query cache.

**Rationale**: The sessions list is already cached in TanStack Query from the Sessions view navigation. The `useCarTracks` hook provides car display name, badge URL, and per-track display names + preview URLs. No new API calls are needed — both data sources are already warm in the cache by the time the user reaches a session detail view (they navigated through Garage → Tracks → Sessions to get there).

**Alternatives considered**:
- Creating a dedicated `GET /sessions/{id}/header` endpoint: Rejected — adds backend work in a frontend-only phase, and all needed data already exists.
- Using `useCarStats()` for car info + a separate track lookup: Rejected — `useCarTracks(car)` provides both car header info (display_name, badge_url, brand, class) and track list in one query, and is already built for Phase 14.2.
- Reading from router params only (no API): Rejected — router params contain raw identifiers (ks_ferrari_488_gt3), not display names. The header needs human-readable names and images.

**Key details**:
- `useSessions()` returns a flat list; filter by `session_id` to find the current session record (car, track, track_config, session_date, lap_count, best_lap_time, state).
- `useCarTracks(car)` returns `TrackStatsListResponse` with car_display_name, car_brand, car_class, badge_url at the top level, plus a tracks array where each entry has track_name, track_config, display_name, preview_url.
- Match the track entry by track_name + track_config to get the display name and preview URL.
- If `useCarTracks` hasn't loaded yet (cold cache), the header shows raw identifiers as fallback and updates when data arrives — standard TanStack Query loading pattern.
- The header renders inside SessionLayout, above the `<Outlet />`, so it persists across tab switches without re-mounting.

## R2: CSS Update Strategy — Token Alignment

**Decision**: Update existing CSS files in-place. No new CSS files created (except SessionHeader.css for the new component). Map prototype Tailwind patterns to existing design tokens. Do not rename CSS classes unless necessary for specificity conflicts.

**Rationale**: The existing CSS already uses design tokens extensively. The gap between current styling and the prototypes is primarily in spacing values, border-radius consistency, and some surface color choices. In-place updates minimize the risk of breaking existing tests that select by CSS class name.

**Alternatives considered**:
- Replacing all CSS with fresh files: Rejected — high risk of regressions, and existing CSS is well-structured.
- Adding a global stylesheet overlay: Rejected — creates specificity conflicts and makes maintenance harder.
- Migrating to CSS Modules or Tailwind: Rejected — the project constitution mandates the current ace-prefix BEM approach with design tokens.

**Key details**:
- Prototype uses `rounded-xl` (12px) for cards → map to `var(--radius-lg)` (already 12px in tokens).
- Prototype uses `bg-dark-surface` → already mapped to `var(--bg-surface)` in tokens.
- Prototype uses `border-dark-border` → already mapped to `var(--border)` in tokens.
- Prototype uses `p-6` (24px) for card padding → map to `var(--space-6)`.
- Prototype uses `gap-6` (24px) between sections → map to `var(--space-6)`.
- The main visual gap is that current CSS uses `--radius-md` (8px) for cards while prototypes use `--radius-lg` (12px), and some spacing uses smaller values than the prototypes suggest.
- Chart grid color in prototypes is `#2A333D` → this matches `var(--border)` in dark theme, already defined.

## R3: Telemetry Chart Color Alignment

**Decision**: Keep current Recharts color props (hardcoded hex in JSX) but align them with the brand palette from tokens.css. The chart stroke colors are passed as props to Recharts `<Line stroke="...">` which requires string hex values, not CSS variables.

**Rationale**: Recharts components accept color strings as props, not CSS variable references. Using `getComputedStyle()` to resolve CSS variables at runtime adds complexity and potential flicker. The brand palette hex values are stable and documented in tokens.css primitives.

**Alternatives considered**:
- Using CSS variables via `getComputedStyle()`: Rejected — adds runtime overhead, potential flash of wrong colors, and doesn't work with Recharts' SVG rendering model.
- Creating a JS color constants file mirroring tokens: Considered — but the current approach of inline hex in chart components is already the pattern used in TelemetryChart.tsx. Documenting the mapping in a comment is sufficient.

**Key details**:
- Current chart colors: green (throttle), red (brake), blue (steering), amber (speed), gray (gear).
- Prototype chart colors: Same semantic mapping — green for throttle, red for brake, cyan/blue for steering, amber/yellow for speed.
- Align to tokens.css primitives: `--green-500` (#22C55E), `--red-500` (#EF4444), `--cyan-500` (#06B6D4), `--amber-500` (#F59E0B), `--gray-500` (#6B7280).
- These hex values appear as hardcoded strings in the Recharts `stroke` prop — this is acceptable because they are documented references to the token primitives, not arbitrary colors.

## R4: EngineerView Hardcoded Color Fix

**Decision**: Replace the single hardcoded `rgba(255, 255, 255, 0.7)` in EngineerView.css (user message timestamp) with a token-based approach. Add a `--text-on-brand` semantic token to tokens.css if one doesn't already exist, or use `color-mix(in srgb, var(--text-primary) 70%, transparent)` for semi-transparent text.

**Rationale**: Constitution Principle XII mandates all colors from design tokens. The user message timestamp needs semi-transparent white text to be readable against the brand-color background. Modern CSS `color-mix()` can achieve this without a new token.

**Key details**:
- Current: `color: rgba(255, 255, 255, 0.7)` — only works in dark theme.
- Fix: `color: color-mix(in srgb, white 70%, transparent)` — still white-ish but can be made theme-aware if needed.
- Alternative: Add `--text-on-brand: rgba(255, 255, 255, 0.85)` to dark theme and `--text-on-brand: rgba(255, 255, 255, 0.95)` to light theme in tokens.css.
- The `color-mix()` approach is simpler and doesn't require a new token, since the user message bubble always has a colored background where white text is appropriate in both themes.

## R5: Settings Layout Approach

**Decision**: Keep the existing single-column card layout for Settings (max-width 720px centered). Do not adopt the prototype's 4-column sidebar navigation pattern.

**Rationale**: The prototype shows a settings layout with a left sidebar navigation (General, Units, Analysis, etc.) and a 3-column content area. However, the current Settings implementation has only 5 sections that fit comfortably in a scrollable single-column layout. Adding sidebar navigation would require significant component restructuring (new SettingsSidebar component, scroll-to-section or sub-routing, active state management) that exceeds the scope of a visual polish phase. The prototype's sidebar pattern is a reference for future work, not a requirement for visual consistency.

**Alternatives considered**:
- Full sidebar navigation like the prototype: Rejected — requires new component code and routing changes, which is out of scope for a CSS-only visual update.
- Collapsible accordion sections: Rejected — adds interactivity not in the current implementation.

**Key details**:
- Update card surfaces, spacing, form element styling, and typography to match the prototype's visual tokens.
- Keep existing vertical card flow with max-width 720px.
- Update form elements (selects, inputs, buttons) to use the rounded-lg/xl border-radius and padding from the prototypes.
- The visual result will look like the prototype's right-side content area but without the left sidebar.

## R6: Test Impact Assessment

**Decision**: Existing tests should pass without modification for the CSS-only changes. Only the new SessionHeader component requires new tests. If any CSS class names are renamed (unlikely), affected test selectors will be updated.

**Rationale**: The test suite uses Testing Library which queries by role, text, and test IDs rather than CSS class names. CSS-only changes (colors, spacing, borders, radius) don't affect DOM structure or text content, so tests won't break.

**Key details**:
- 23 existing frontend test files across all views.
- Tests query by: `getByText`, `getByRole`, `getAllByRole`, `getByTestId`, `getByPlaceholderText`.
- No tests query by CSS class name (e.g., `querySelector('.ace-card')`) — they use Testing Library idioms.
- New test: `SessionHeader.test.tsx` — verifies car/track info rendering, status badge, stats display, fallback behavior.
- SessionLayout.test.tsx may need minor updates if the layout wrapper gains the SessionHeader child.
