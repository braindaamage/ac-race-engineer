# UI Contract: Design Token Updates

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15

## Primitive Token Changes

All changes are in `frontend/src/tokens.css`, Layer 1 (Primitives).

### Color Primitives

| Token | Before | After |
|-------|--------|-------|
| `--red-500` | #ef4444 | #FF1A1A |
| `--red-600` | #dc2626 | #E60000 |
| `--red-700` | #b91c1c | #CC0000 |
| `--cyan-400` | #22d3ee | #33D6FF |
| `--cyan-500` | #06b6d4 | #00CCFF |
| `--cyan-600` | #0891b2 | #00A3CC |
| `--green-400` | #4ade80 | #2ECC71 |
| `--green-500` | #22c55e | #1AB866 |
| `--green-600` | #16a34a | #159652 |
| `--amber-400` | #fbbf24 | #FFC733 |
| `--amber-500` | #f59e0b | #FFB917 |
| `--amber-600` | #d97706 | #CC9412 |
| `--blue-500` | #3b82f6 | #3B82F6 (unchanged) |
| `--blue-600` | #2563eb | #2563EB (unchanged) |

### Gray Scale Primitives

| Token | Before | After |
|-------|--------|-------|
| `--gray-50` | #f8fafc | #F3F4F6 |
| `--gray-100` | #f1f5f9 | #E5E7EB |
| `--gray-200` | #e2e8f0 | #D1D5DB |
| `--gray-300` | #cbd5e1 | #9CA3AF |
| `--gray-400` | #94a3b8 | #7A8B99 |
| `--gray-500` | #64748b | #6B7280 |
| `--gray-600` | #475569 | #4B5563 |
| `--gray-700` | #334155 | #2A333D |
| `--gray-800` | #1e293b | #222D38 |
| `--gray-900` | #0f172a | #171E27 |
| `--gray-950` | #020617 | #0B1015 |

## Semantic Layer Impact

The semantic layer (Layer 2) references primitives via `var(--gray-950)` etc. For the dark theme, updating primitives propagates automatically through existing mappings.

The semantic layer requires targeted overrides for the light theme. Because the gray primitive values shifted (e.g., `--gray-900` moved from `#0f172a` to `#171E27`), some light-theme semantic tokens that reference gray primitives will not match the prototype's light palette. The following light-theme semantic overrides are needed:

| Token | Current mapping | New explicit value | Reason |
|-------|----------------|-------------------|--------|
| Light `--text-primary` | var(--gray-900) → #171E27 | #111827 | Prototype specifies #111827 for light text |
| Light `--text-secondary` | var(--gray-600) → #4B5563 | #6B7280 | Prototype specifies #6B7280 for light subtext |
| Light `--border` | var(--gray-200) → #D1D5DB | #E5E7EB | Prototype specifies #E5E7EB for light borders |

These three overrides are applied directly in the light theme block of `tokens.css` using explicit hex values instead of primitive references.

## Undefined Token Fixes

These tokens are referenced by components but not defined in `tokens.css`. Each must be fixed in the component CSS files that reference them.

| Undefined Reference | Fix | Files |
|--------------------|-----|-------|
| `var(--spacing-lg)` | Replace with `var(--space-6)` | CompareView.css (×2), AnalysisView.css (×2), SessionsView.css (×2) |
| `var(--brand)` | Replace with `var(--color-brand)` | Settings.css (×1), OnboardingWizard.css (×4) |
| `var(--success)` | Replace with `var(--color-positive)` | OnboardingWizard.css (×1) |
| `var(--error)` | Replace with `var(--color-error)` | OnboardingWizard.css (×1) |
| `var(--border-primary)` | Replace with `var(--border-strong)` | AnalysisView.css (×1) |
| `var(--border-subtle)` | Replace with `var(--border)` | CompareView.css (×1), AnalysisView.css (×1) |
| `var(--color-success)` | Replace with `var(--color-positive)` | CompareView.css (×1), AnalysisView.css (×1) |
| `var(--font-size-md)` | Replace with `var(--font-size-base)` | Settings.css (×1), CarDataSection.css (×1), AppShell.css (×1), OnboardingWizard.css (×1) |

**Total**: 23 replacements across 7 files.

## New Tokens (if needed)

No new tokens are anticipated. The existing token vocabulary is sufficient for the new header, breadcrumb, and tab bar components. All styling will reference existing semantic tokens.

## Font Stack

No changes to font definitions. The existing `--font-ui` (Inter) and `--font-mono` (JetBrains Mono) tokens remain. Font files are already bundled as local woff2.

## Icon Font Addition

`@fortawesome/fontawesome-free` is added as an npm dependency. Its CSS is imported globally once (in `main.tsx` or `App.tsx`). Icons are used via CSS classes in JSX (`<i className="fa-solid fa-gear" />`), not via React components. This avoids a heavier `@fortawesome/react-fontawesome` dependency.
