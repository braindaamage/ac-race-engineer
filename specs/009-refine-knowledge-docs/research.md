# Research: Refine Knowledge Base Documents

**Branch**: `009-refine-knowledge-docs` | **Date**: 2026-03-05

## R1: Current State of Errors in Knowledge Base

**Decision**: The audit report (`docs/AUDIT_REPORT.md`) is confirmed as accurate after direct verification against the source files.

**Findings**:

| Issue | Confirmed? | Details |
|-------|-----------|---------|
| Pacejka/Magic Formula references | **Not found** | No explicit Pacejka references exist in any document. The tire model is described generically without naming AC's brush model specifically. The fix is to add explicit brush model description, not remove Pacejka references. |
| Springs control transfer speed | **Confirmed** | `suspension_and_springs.md` line 7: "springs govern the transient rate of transfer, not the final magnitude" — this is the inverted attribution the audit flags. |
| Spring rate vs wheel rate confusion | **Confirmed** | `suspension_and_springs.md` line 20 describes "Spring rate is the fundamental stiffness of the coil or torsion bar spring, measured in N/mm" without noting AC uses wheel rates. |
| Ramp angles in drivetrain.md | **Confirmed** | Lines 11, 13, 14, 20-21: "Power and Coast Ramp Angles" heading, "ramp angles (measured in degrees)", "steeper/shallower ramp" terminology. The Adjustable Parameters section (line 33+) already correctly uses lock percentages — creating internal inconsistency. |
| Brake ducts/pad compounds universal | **Confirmed** | `braking.md` lines 23-27: brake ducts, pad compounds, and engine brake maps presented as standard tuning parameters without car-specific availability notes. |
| 20-30 Hz sample rate | **Confirmed** | `telemetry_and_diagnosis.md` line 7: "approximately 20-30 Hz" stated as THE capture rate. |
| vehicle_balance_fundamentals.md transfer speed | **Partially** | Line 34: "controls how quickly the body rolls" is about body roll rate, not load transfer speed per se. The attribution is imprecise but less directly wrong than suspension_and_springs.md. |

**Alternatives considered**: None — the audit report is the authoritative source. Direct file verification confirms all major findings.

## R2: Loader and Test Constraints

**Decision**: Content-only edits are safe. Section titles must not change.

**Rationale**:
- `loader.py` validates only that 4 section headings exist: "Physical Principles", "Adjustable Parameters and Effects", "Telemetry Diagnosis", "Cross-References"
- Content within sections is free-form text parsed as a single string
- `index.py` maps `document_name → section_title → [tags]` — tags are used for search retrieval
- Tests verify: document loading, section parsing, search functionality, signal mapping, caching, deduplication, template validation
- No test validates specific content within sections — only that sections exist and are non-empty

**Constraints**:
- Section titles MUST remain exactly: "Physical Principles", "Adjustable Parameters and Effects", "Telemetry Diagnosis", "Cross-References"
- Document filenames MUST not change
- Adding content within sections is always safe for the loader
- KNOWLEDGE_INDEX tag changes only affect search ranking, not loading

## R3: Scope of KNOWLEDGE_INDEX Tag Updates

**Decision**: Expand tags only for significantly new content areas not covered by existing tags.

**Rationale**: The current tags already cover most concepts mentioned in the audit corrections. New content areas that would benefit from tag additions:

| Document | New Content | Tags to Add |
|----------|-------------|-------------|
| tyre_dynamics.md | Brush model, tire load sensitivity, pneumatic trail, SAT, relaxation length, camber thrust | `"brush model"`, `"pneumatic trail"`, `"self-aligning torque"`, `"relaxation length"`, `"camber thrust"` |
| vehicle_balance_fundamentals.md | Weight transfer decomposition, TLLTD, transient vs steady-state | `"TLLTD"`, `"roll center"`, `"transient"`, `"steady state"` |
| suspension_and_springs.md | Wheel rate vs spring rate, anti-geometry, roll center migration | `"wheel rate"`, `"anti-dive"`, `"anti-squat"`, `"roll center"` |
| dampers.md | Velocity domains, damping ratio, rebound:compression ratio, platform control | `"damping ratio"`, `"velocity domain"`, `"platform control"`, `"packing down"` |
| drivetrain.md | Lock percentages (AC-specific), trail braking interaction | `"lock percentage"`, `"trail braking"` |
| telemetry_and_diagnosis.md | G-G diagram, reference lap, hypothesis generation | `"g-g diagram"`, `"friction circle"`, `"reference lap"` |
| aero_balance.md | CoP vs CoG, L/D ratio, independent wing model | `"center of pressure"`, `"lift to drag"`, `"efficiency"` |
| alignment.md | Dynamic camber, camber thrust | `"dynamic camber"`, `"camber thrust"`, `"camber gain"` |

**Alternatives considered**: Full tag overhaul — rejected because existing tags are functional and minimal changes preserve backward compatibility.

## R4: drivetrain.md Internal Inconsistency

**Decision**: Unify on AC's lock percentage model throughout. Remove ramp angle terminology from Physical Principles section to match the Adjustable Parameters section which already uses lock percentages.

**Rationale**: The Physical Principles section (lines 11-21) uses "ramp angles" extensively while the Adjustable Parameters section (lines 33-46) correctly uses "Differential Lock Percentage (Power/Coast)". This internal inconsistency must be resolved by rewriting the Physical Principles LSD description to use lock percentages, noting that ramp angles are a real-world concept but not how AC parametrizes its model.

## R5: Content Already Correct (No Changes Needed)

Several items the audit flagged as "probable" errors turn out to be less severe in the actual documents:

- **vehicle_balance_fundamentals.md Spring Rates section** (line 34): Describes springs affecting "how quickly the body rolls" and "amplitude of load transfer" — this is imprecise but not the direct springs→transfer-speed error. Will refine to be more precise.
- **dampers.md**: Already correctly attributes transient load transfer control to dampers (line 35). Confirmed correct.
- **tyre_dynamics.md**: No Pacejka references exist, but the tire model is described generically. Will add explicit brush model identification.
