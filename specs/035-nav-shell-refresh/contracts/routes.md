# UI Contract: Route Map

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15

## Route Definitions

All routes are client-side (no server routing). The Tauri webview serves the SPA from a single entry point.

### Route Tree

```
/                                                → Navigate to /garage (redirect)
/garage                                          → GarageView (placeholder)
/garage/:carId/tracks                            → CarTracksView (placeholder)
/garage/:carId/tracks/:trackId/sessions          → SessionsView
/session/:sessionId                              → Navigate to /session/:sessionId/laps (redirect)
/session/:sessionId/laps                         → AnalysisView
/session/:sessionId/setup                        → CompareView
/session/:sessionId/engineer                     → EngineerView
/settings                                        → SettingsView
*                                                → Navigate to /garage (catch-all)
```

### Layout Hierarchy

```
Root Layout (AppShell: Header + Breadcrumb + TabBar + Outlet + ToastContainer)
├── /garage                    → GarageView
├── /garage/:carId/tracks      → CarTracksView
├── /garage/:carId/tracks/:trackId/sessions → SessionsView
├── /session/:sessionId        → SessionLayout (tab bar + Outlet)
│   ├── laps                   → AnalysisView
│   ├── setup                  → CompareView
│   └── engineer               → EngineerView
├── /settings                  → SettingsView
└── *                          → Redirect to /garage
```

### Route Parameters

| Parameter | Type | Encoding | Example |
|-----------|------|----------|---------|
| `:carId` | string | URL-encoded car identifier | `ks_bmw_m3_e30` |
| `:trackId` | string | URL-encoded track identifier | `magione` |
| `:sessionId` | string | Session UUID or timestamp-based ID | `20260315_140523_ks_bmw_m3_e30_magione` |

### Navigation Actions

| From | Action | Target Route |
|------|--------|-------------|
| Garage Home | Click car card | `/garage/{carId}/tracks` |
| Car Tracks | Click track card | `/garage/{carId}/tracks/{trackId}/sessions` |
| Sessions | Click session card | `/session/{sessionId}/laps` |
| Session Detail | Click tab | `/session/{sessionId}/{tab}` |
| Any page | Click header settings icon | `/settings` |
| Any page | Click breadcrumb "Home" | `/garage` |
| Any page | Click breadcrumb car segment | `/garage/{carId}/tracks` |
| Any page | Click breadcrumb track segment | `/garage/{carId}/tracks/{trackId}/sessions` |
| Settings | Browser back | Previous route |

### Breadcrumb Contract

The breadcrumb always displays segments from root to current position:

| Route | Breadcrumb |
|-------|-----------|
| `/garage` | **Home** |
| `/garage/:carId/tracks` | [Home] / **{carName}** |
| `/garage/:carId/tracks/:trackId/sessions` | [Home] / [{carName}] / **{trackName}** |
| `/session/:sessionId/*` | [Home] / [{carName}] / [{trackName}] / **{sessionLabel}** |
| `/settings` | [Home] / **Settings** |

Bracketed segments are clickable links. Bold segment is the current page (not clickable).

### Tab Bar Contract

| Route Level | Tab Bar Content |
|-------------|----------------|
| `/garage` | Garage Home (active) · Tracks · Sessions · Settings |
| `/garage/:carId/tracks` | Garage Home · Tracks (active) · Sessions · Settings |
| `/garage/:carId/tracks/:trackId/sessions` | Garage Home · Tracks · Sessions (active) · Settings |
| `/session/:sessionId/*` | Lap Analysis · Setup Compare · Engineer (active determined by route suffix) |
| `/settings` | Garage Home · Tracks · Sessions · Settings (active) |

At the garage/tracks/sessions level, the tab bar shows global navigation tabs. At the session detail level, it switches to the three work tabs. The Settings tab appears in the global navigation tabs. Active tab is determined by the current route.
