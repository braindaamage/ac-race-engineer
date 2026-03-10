# Quickstart: Skill Prompt Optimization

**Feature**: 027-skill-prompt-optimization
**Date**: 2026-03-09

## What to Implement

Edit 5 markdown files in `backend/ac_engineer/engineer/skills/`. No Python code, tests, API, or frontend changes.

## Files to Modify

| File | Changes |
|------|---------|
| `balance.md` | Add Output Requirements (max 3 changes, 1-2 sentence reasoning with data citation, 1 sentence effect). Add Priority Tiers. Remove `get_current_value` from Tool Usage. Move `search_kb` to end with pre-loaded note. |
| `tyre.md` | Same as balance.md |
| `aero.md` | Same as balance.md |
| `technique.md` | Add Output Requirements (max 3 DriverFeedback, 1 sentence observation with data, 1-2 sentence suggestion). Add Priority Tiers. |
| `principal.md` | Add Output Requirements (2-3 sentence summary, no physics re-explanation, no setup changes). Add Tool Usage (get_lap_detail, get_corner_metrics for verification only). |

## Priority Tiers Section (shared by all specialists)

Three tiers for signal evaluation:
1. **Propose**: Signal confirmed in majority of flying laps (or both laps if session has 2-3)
2. **Mention with low confidence**: Signal in 1 lap only or data is partial
3. **Omit**: Signal marginal, data absent, or outside this agent's domain

## Verification

1. Run existing tests: `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v` — all 167 tests must pass
2. Run a real analysis with Gemini 2.5 Flash on the same test session used for the ~14,400 token baseline
3. Verify output tokens are under 7,000 (SC-001)
4. Spot-check that each setup change has a data citation and single-sentence effect
