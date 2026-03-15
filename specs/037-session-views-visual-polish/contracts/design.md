# Design Contracts: Session Views Visual Polish

**Branch**: `037-session-views-visual-polish` | **Date**: 2026-03-15

## Overview

No new API endpoints. This document defines the visual design contracts — the CSS token mappings, component styling rules, and layout patterns that all views must follow to achieve visual consistency.

## Design Token Mapping (Prototype → Production)

The prototypes use Tailwind CSS classes. The production CSS uses `var()` references to design tokens in `tokens.css`. This table maps the key prototype patterns to their token equivalents.

### Surface & Background

| Prototype Class | Token Variable | Dark Value | Light Value | Usage |
|----------------|---------------|------------|-------------|-------|
| `bg-dark-bg` | `var(--bg)` | `var(--gray-950)` | `#F8F9FA` | Page background |
| `bg-dark-surface` | `var(--bg-surface)` | `var(--gray-900)` | `#ffffff` | Card/component background |
| `bg-dark-elevated` | `var(--bg-elevated)` | `var(--gray-800)` | `var(--gray-100)` | Hover states, elevated panels |
| `hover:bg-dark-border/30` | `var(--bg-hover)` | `var(--gray-800)` | `var(--gray-200)` | Row/item hover |

### Text

| Prototype Class | Token Variable | Dark Value | Light Value | Usage |
|----------------|---------------|------------|-------------|-------|
| `text-white` / `text-dark-text` | `var(--text-primary)` | `var(--gray-50)` | `#111827` | Primary text |
| `text-dark-subtext` | `var(--text-secondary)` | `var(--gray-300)` | `#6B7280` | Secondary/label text |
| `text-brand-grey` | `var(--text-muted)` | `var(--gray-500)` | `var(--gray-400)` | Muted/disabled text |

### Borders

| Prototype Class | Token Variable | Dark Value | Light Value | Usage |
|----------------|---------------|------------|-------------|-------|
| `border-dark-border` | `var(--border)` | `var(--gray-800)` | `#E5E7EB` | Standard borders |
| (stronger variant) | `var(--border-strong)` | `var(--gray-700)` | `var(--gray-300)` | Table headers, dividers |

### Brand Colors

| Prototype Class | Token Variable | Usage |
|----------------|---------------|-------|
| `brand-red` (#E60000) | `var(--color-brand)` | Primary actions, active states |
| `brand-blue` (#00CCFF) | `var(--color-ai)` | AI content, secondary accent |
| `brand-green` (#1AB866) | `var(--color-positive)` | Success, improvements |
| `brand-amber` (#FFB917) | `var(--color-warning)` | Warnings, caution |
| `text-red-400` | `var(--color-error)` | Errors, degradation |
| `text-blue-400` | `var(--color-info)` | Informational content |

### Spacing

| Prototype Class | Token Variable | Value | Usage |
|----------------|---------------|-------|-------|
| `p-4` | `var(--space-4)` | 16px | Standard component padding |
| `p-6` | `var(--space-6)` | 24px | Card content padding |
| `gap-4` | `var(--space-4)` | 16px | Grid/flex gap (compact) |
| `gap-6` | `var(--space-6)` | 24px | Section gap (standard) |

### Border Radius

| Prototype Class | Token Variable | Value | Usage |
|----------------|---------------|-------|-------|
| `rounded-lg` | `var(--radius-md)` | 8px | Buttons, inputs, small elements |
| `rounded-xl` | `var(--radius-lg)` | 12px | Cards, panels, large containers |

## Component Styling Contracts

### Card Surfaces

All card-like containers across all views MUST use:
```css
background: var(--bg-surface);
border: 1px solid var(--border);
border-radius: var(--radius-lg);  /* 12px — updated from radius-md */
```

### Table Styling

All data tables MUST use:
```css
/* Table */
width: 100%;
border-collapse: collapse;

/* Header cells */
th {
  text-align: left;
  padding: var(--space-3) 0;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-strong);
}

/* Data cells */
td {
  padding: var(--space-3) 0;
  font-size: var(--font-size-sm);
  border-bottom: 1px solid var(--border);
}

/* Row hover */
tbody tr:hover {
  background: var(--bg-hover);
}
```

### Interactive List Items (Lap List, Stint Selector)

All selectable list items MUST use:
```css
/* Base */
padding: var(--space-3) var(--space-4);
border-radius: var(--radius-md);
cursor: pointer;
transition: background var(--transition-fast), border-color var(--transition-fast);

/* Hover */
:hover {
  background: var(--bg-hover);
}

/* Selected */
.--selected {
  background: var(--bg-elevated);
  border-left: 3px solid var(--color-brand);
}
```

### Form Elements (Settings, Chat Input)

All form inputs and selects MUST use:
```css
background: var(--bg);
border: 1px solid var(--border);
border-radius: var(--radius-md);
padding: var(--space-2) var(--space-3);
color: var(--text-primary);
font-size: var(--font-size-sm);

:focus {
  outline: none;
  border-color: var(--color-ai);
}
```

### Status Badges

Session state displayed in the header badge:
- `discovered` → Badge variant `neutral`
- `parsed` → Badge variant `neutral`
- `analyzed` → Badge variant `info`
- `engineered` → Badge variant `success`

## SessionHeader Component Contract

### Props

```typescript
interface SessionHeaderProps {
  session: SessionRecord;
  carDisplayName: string;
  carBadgeUrl: string | null;
  trackDisplayName: string;
  trackPreviewUrl: string | null;
}
```

### Visual Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Car Badge]  Car Display Name        [Track Preview]  Track Name   │
│              Brand • Class            Country                      │
│                                                                    │
│  📅 Session Date    🏁 N laps    ⏱ Best Lap Time    [Status Badge]│
└─────────────────────────────────────────────────────────────────────┘
```

### CSS Classes

- `.ace-session-header` — root container
- `.ace-session-header__car` — car badge + name section
- `.ace-session-header__track` — track preview + name section
- `.ace-session-header__stats` — session statistics row
- `.ace-session-header__badge` — car/track image (with fallback)

### Image Fallback

- Car badge: On error → Font Awesome `fa-car` icon in a colored circle
- Track preview: On error → Font Awesome `fa-road` icon in a colored circle
- Pattern matches GarageView and CarTracksView fallback approach from Phase 14.2

## Chart Color Contract

Recharts line stroke colors aligned with brand palette:

| Channel | Hex Value | Token Reference | Prototype Match |
|---------|-----------|----------------|-----------------|
| Throttle | `#22C55E` | `--green-500` | brand-green |
| Brake | `#EF4444` | `--red-500` | brand-red |
| Steering | `#06B6D4` | `--cyan-500` | brand-blue |
| Speed | `#F59E0B` | `--amber-500` | brand-amber |
| Gear | `#6B7280` | `--gray-500` | brand-grey |

These appear as hardcoded hex strings in Recharts `stroke` props (Recharts doesn't support CSS variables). This is the only permitted exception to the no-hardcoded-hex rule, documented here.
