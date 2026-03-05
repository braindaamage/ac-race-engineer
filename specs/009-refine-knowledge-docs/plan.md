# Implementation Plan: Refine Knowledge Base Documents

**Branch**: `009-refine-knowledge-docs` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-refine-knowledge-docs/spec.md`

## Summary

Correct factual errors, fill content gaps, and ensure AC-specific accuracy across 10 vehicle dynamics knowledge base markdown documents. Apply corrections from `docs/AUDIT_REPORT.md` in priority order. Update KNOWLEDGE_INDEX tags where new content areas are added. All 48 existing tests must continue passing.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`) — for running tests only
**Primary Dependencies**: None — this is a content-only change to markdown files and a Python dict
**Storage**: N/A — files edited in place
**Testing**: pytest (48 existing knowledge tests in `backend/tests/knowledge/`)
**Target Platform**: Windows 11 (development), content consumed by Pydantic AI agents at runtime
**Project Type**: Content refinement within existing knowledge base subsystem
**Performance Goals**: N/A — no runtime code changes
**Constraints**: 4-section document structure must be preserved; section titles must not change; document filenames must not change
**Scale/Scope**: 10 markdown documents + 1 Python index file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Correcting knowledge base errors improves data integrity of LLM context |
| II. Car-Agnostic Design | PASS | Corrections add car-specific availability notes (not hardcoded logic) and remove falsely universal parameter claims |
| III. Setup File Autonomy | N/A | No setup file changes |
| IV. LLM as Interpreter | PASS | Knowledge base provides better factual grounding for LLM interpretation role |
| V. Educational Explanations | PASS | Corrected physics explanations improve educational quality |
| VI. Incremental Changes | PASS | Documents refined individually in priority order |
| VII. CLI-First MVP | N/A | No CLI changes |
| VIII. API-First Design | N/A | No API changes |
| IX. Separation of Concerns | PASS | Changes stay within knowledge/ subsystem |
| X. Desktop App Stack | N/A | No desktop changes |
| XI. LLM Provider Abstraction | N/A | No provider changes |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/009-refine-knowledge-docs/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md
```

### Source Code (files modified)

```text
backend/ac_engineer/knowledge/
├── docs/
│   ├── tyre_dynamics.md                  # Priority 1 — brush model, load sensitivity, SAT
│   ├── vehicle_balance_fundamentals.md   # Priority 2 — transfer attribution, TLLTD
│   ├── telemetry_and_diagnosis.md        # Priority 3 — sample rate, G-G diagram
│   ├── suspension_and_springs.md         # Priority 4 — wheel rate, roll center
│   ├── drivetrain.md                     # Priority 5 — lock percentages
│   ├── braking.md                        # Priority 6 — car-specific availability
│   ├── dampers.md                        # Priority 7 — velocity domains, AC params
│   ├── alignment.md                      # Priority 8 — dynamic camber, adjustable vs fixed
│   ├── aero_balance.md                   # Priority 9 — AC aero model, CoP, L/D
│   └── setup_methodology.md             # Priority 10 — OVAT limits, lap count
└── index.py                              # Tag expansion in KNOWLEDGE_INDEX
```

**Structure Decision**: No new files or directories. All changes are edits to existing files within the established `knowledge/` package structure.

## Implementation Phases

### Phase A: Priority 1-2 Documents (Foundation)

These two documents contain the most severe errors and are referenced by all other documents. Must be corrected first to establish the correct factual baseline.

**A1. Edit `tyre_dynamics.md`** (Priority 1)

Physical Principles section:
- Add explicit identification of AC's brush-based tire model (bristle deformation, adhesion/sliding regions, Coulomb friction) at the beginning. Note that Pacejka Magic Formula is the industry standard but AC deliberately chose a physics-based approach.
- Add **Tire Load Sensitivity** subsection: explain concave Fy-Fz relationship, that effective friction coefficient decreases with load. Include conceptual numeric example (two tires at equal load vs unequal load producing less total force).
- Add **Pneumatic Trail and Self-Aligning Torque** subsection: trail decreases with slip angle, reaches zero near adhesion limit, explains steering wheel lightening as primary FFB indicator of grip limit in AC.
- Add **Relaxation Length** subsection: distance tire must roll for lateral force to reach ~63% of steady-state value. AC models this explicitly via RELAXATION_LENGTH parameter. Affects transient response.
- Add **Camber Thrust** subsection: lateral force from tire inclination independent of slip angle. Explains why negative camber benefits outer wheel in corners.
- Expand **Combined Slip** content: interaction follows approximately elliptical envelope, forces trade off continuously (not binary).

Adjustable Parameters section:
- Add note about AC's thermal model: core temperature (higher inertia) vs surface inner/mid/outer temperatures. Surface temps available via Python API only (not shared memory in AC original).

Telemetry Diagnosis section:
- Add SAT/FFB torque as diagnostic signal for tire saturation
- Add wheel load per wheel (`wheelLoad[4]`) for load sensitivity analysis
- Add hot pressure monitoring (AC models pressure changes with temperature)

Cross-References section:
- No structural changes needed; content already references relevant docs

**A2. Edit `vehicle_balance_fundamentals.md`** (Priority 2)

Physical Principles section:
- Add **Tire Load Sensitivity as Mediator** subsection after the existing "Neutral Steer and Load Sensitivity" paragraph. Expand the brief mention into a clear explanation that load sensitivity is THE mechanism by which weight transfer distribution affects balance. The concave Fy-Fz curve means the more heavily loaded axle loses proportionally more grip.
- Add **Weight Transfer Decomposition** subsection: three components — geometric (via roll center, instantaneous), elastic (via springs/ARBs, proportional to roll stiffness distribution), unsprung mass. Explain that ride height affects roll center position, making it a powerful tuning tool beyond just CG height and aero.
- Add **TLLTD** concept: Total Lateral Load Transfer Distribution unifies springs, ARBs, and suspension geometry effects. Approximate rule: TLLTD front ≈ static weight distribution front + ~5%.
- Add **Transient vs Steady-State Balance** clarification: springs/ARBs control steady-state LLTD magnitude and distribution; dampers control the transient rate. These are distinct phenomena requiring different tuning approaches.

Adjustable Parameters — Spring Rates subsection:
- Refine wording: clarify that stiffer springs increase roll stiffness at that axle (shifting LLTD), but do NOT control the speed/rate of weight transfer (that's dampers). Current wording "controls how quickly the body rolls" is about body roll rate, not load transfer rate — make this distinction explicit.

Adjustable Parameters — Differential Settings subsection:
- Replace "high-ramp-angle" with "high lock percentage" to match AC terminology
- Note that AC uses POWER/COAST lock percentages (0.0-1.0), not ramp angles

Cross-References — drivetrain.md entry:
- Replace "ramp angles" with "lock percentages"

### Phase B: Priority 3-4 Documents (Telemetry & Suspension)

**B1. Edit `telemetry_and_diagnosis.md`** (Priority 3)

Physical Principles section:
- Correct sample rate: replace "approximately 20-30 Hz" with accurate description — physics engine runs at ~333 Hz internally; telemetry capture tools log at 30-200 Hz depending on the tool and configuration.
- Add note that events shorter than sampling interval may be under-resolved, adjusted for correct rate range.
- Add **Telemetry Tools Ecosystem** subsection: mention key tools (ACTI legacy ~20 Hz, Telemetrick 30-200 Hz with 180+ channels, MoTeC i2 Pro as analysis software). Note Telemetrick as recommended primary tool.

Adjustable Parameters section:
- No significant changes needed

Telemetry Diagnosis section:
- Add **G-G Diagram** subsection: plot lateral vs longitudinal G to visualize grip utilization and identify under-used performance envelope areas.
- Add **Reference Lap Methodology** subsection: compare own data against reference (fastest personal lap or telemetry from another driver via Telemetry Exchange). Overlay traces, identify where time is gained/lost.
- Reframe symptom-cause table header and intro text: present as "hypothesis generator" not definitive diagnosis. Add note about equifinalidad (multiple causes produce identical symptoms), speed dependence (mechanical vs aero), and driver technique masking/mimicking setup problems.
- Add note that brake duct references are car-specific (not available on all cars)

Cross-References section:
- No structural changes needed

**B2. Edit `suspension_and_springs.md`** (Priority 4)

Physical Principles section:
- Fix line 7 "springs govern the transient rate of transfer": replace with correct attribution — springs and ARBs determine the magnitude and distribution of steady-state lateral load transfer (LLTD). Dampers control the transient rate at which that transfer occurs.
- Add explicit note: "In Assetto Corsa, the SPRING_RATE parameter in setup files and in-game adjustment screens represents wheel rate (stiffness measured at the wheel), not spring rate at the physical coil spring. Wheel rate = spring rate x (motion ratio)^2. All values discussed here refer to wheel rate as AC presents it."
- Add **Ride Height, Roll Center, and Balance** subsection: explain that changing ride height shifts roll center position, which alters the geometric component of lateral load transfer. This makes ride height a powerful balance tuning tool beyond CG height and aero effects.
- Add **Anti-Geometry** brief subsection: anti-dive, anti-squat from suspension geometry. Not user-adjustable in AC but explains why different cars react differently to braking/acceleration pitch.
- Expand bump stop content: note AC models bump stops with progressive rate (`BUMPSTOP_RATE`, `BUMPSTOP_UP`). In aero cars, bump stops are active tuning elements for platform control, not just emergency travel limiters.
- Add natural frequency reference table by vehicle category (street 0.5-1.5 Hz, rally 1.5-2.0, non-aero race 1.5-2.5, GT3 2.5-3.5, high downforce 3.5-5.0+) with formula f = (1/2pi) * sqrt(K_wheel / m_corner_sprung).

Adjustable Parameters section:
- Line 20: change "Spring rate is the fundamental stiffness of the coil or torsion bar spring" to clarify AC uses wheel rate
- Add note about motion ratios not being an explicit parameter in AC (derived from suspension geometry coordinates)

Telemetry Diagnosis section:
- Add bump stop contact events (identifiable by abrupt spikes in wheel load or travel hitting limits)
- Add pitch angle (front-rear ride height differential) under braking/acceleration

### Phase C: Priority 5-6 Documents (Drivetrain & Braking)

**C1. Edit `drivetrain.md`** (Priority 5)

Physical Principles section:
- Rewrite LSD subsection (lines 11-21): replace all "ramp angle" / "ramp configuration" terminology with AC's lock percentage model. Explain: "AC models a clutch-pack LSD with POWER and COAST parameters ranging from 0.0 (fully open) to 1.0 (fully locked/spool). This is a simplified model; real ramp angles and Torsen mechanisms are not directly represented."
- Rewrite 1-way/1.5-way/2-way descriptions using lock percentages: 1-way = COAST near 0, POWER > 0; 1.5-way = COAST < POWER; 2-way = COAST = POWER. Clarify that 2-way means equal lock percentage in both directions, NOT fully locked.
- Replace "Power and Coast Ramp Angles" heading with "Power and Coast Lock Behavior" or similar (note: this is a bold subheading within a section, not a `## ` heading, so it does not affect the loader)
- Add note: AC does not model Torsen/helical gear differentials explicitly; the clutch-type model can approximate general behavior but lacks speed-differential sensitivity.
- Separate preload explanation: preload (in Nm) is a constant base locking torque independent of throttle/brake, while POWER/COAST lock is proportional to drivetrain torque.

Adjustable Parameters section:
- Already uses lock percentages (lines 33-46) — verify consistency and add Nm units for preload where missing
- Add brief gear ratio optimization guidance: RPM drop between gears, keeping engine in peak power band

Telemetry Diagnosis section:
- Add wheel speed ratio (not just difference) as diagnostic for diff locking state
- Add correlation of throttle application rate with wheelspin onset

Cross-References section:
- No structural changes needed

**C2. Edit `braking.md`** (Priority 6)

Physical Principles section:
- Add physics of lock-up: transition from dynamic to kinetic friction, ~10-30% grip reduction
- Add deceleration G reference by category (street 0.8-1.0g, GT3 1.2-1.5g, open-wheel 2.0-3.5g, F1 4.0-6.0g)
- Expand trail braking: maintaining partial brake pressure during turn-in keeps weight on front axle (preserving front grip) and exploits friction ellipse for simultaneous lateral+longitudinal force

Adjustable Parameters section:
- Add car-specific availability notes for brake ducts: "Available on some cars in AC; not universal. In ACC, all cars have adjustable brake duct size (scale 0-6)."
- Add car-specific note for pad compounds: "Not available as a setup parameter in AC original. ACC offers 4 pad compound options."
- Add car-specific note for engine brake: "Adjustable only on specific cars (formula cars, some GTs with ECU). Not a universal parameter."
- Add note about brake fade: "Modeled only for specific cars in AC (primarily classic cars: Shelby Cobra, Lotus 49, Maserati 250F, etc.). Most modern cars in AC have unlimited brake endurance."
- Add brake bias ideal calculation concept: front load under braking = static front weight + (mass x deceleration x CG height / wheelbase)

Telemetry Diagnosis section:
- Add individual wheel speed differential during braking as diagnostic for effective brake bias
- Add brake pressure vs deceleration G correlation for fade detection

### Phase D: Priority 7-8 Documents (Dampers & Alignment)

**D1. Edit `dampers.md`** (Priority 7)

Physical Principles section:
- Add AC's bilineal damping model description with actual parameter names: DAMP_BUMP, DAMP_FAST_BUMP, DAMP_FAST_BUMPTHRESHOLD (and rebound equivalents). Two-slope model with a knee point.
- Add **Velocity Domain Framework** subsection: low-speed (0-50 mm/s, body control: roll, pitch, heave — most critical for driver feel and balance), mid-speed (50-200 mm/s, transitions), high-speed (200+ mm/s, bump absorption — must be soft enough for tire contact).
- Note that damper values in AC are expressed at the wheel (consistent with wheel rates for springs).
- Add target damping ratio guidance: race cars typically ζ ≈ 0.65-0.7 (minimizes settling time with minimal overshoot). Street cars 0.2-0.5.
- Add rebound:compression ratio: typical competition range 1.5:1 to 3:1. Rebound controls rate of load release from compressed wheel. Excessive rebound causes "packing down" (suspension not fully extending between compressions).

Adjustable Parameters section:
- Add wheel load variation as key damper performance metric: minimizing load fluctuation maximizes average grip (via tire load sensitivity)
- Add platform control concept for aero cars

Telemetry Diagnosis section:
- Add damper velocity histograms (time distribution across velocity domains)
- Add wheel load coefficient of variation (std dev / mean per wheel)

**D2. Edit `alignment.md`** (Priority 8)

Physical Principles section:
- Add clear distinction: "In AC, camber and toe are adjustable in the setup screen. Caster is adjustable only on some cars (if the range is defined in setup.ini). KPI, scrub radius, and Ackermann geometry are emergent properties of the suspension geometry defined by 3D attachment point coordinates in suspensions.ini — editable only by modders, not in the in-game setup."
- Add **Dynamic Camber** subsection: static camber is only the starting point; what matters is camber under cornering load. Three contributors: geometry gain (FVSA length), caster-induced camber (caster generates negative camber on outer wheel when steering), suspension travel dependent. AC models all via kinematic solver.
- Add **Camber Thrust** subsection: lateral force from tire inclination alone, independent of slip angle.
- Add typical camber reference values: street -0.5 to -1.5 deg, GT/touring -2.0 to -3.5, open-wheel -2.5 to -4.0
- Add brief **Ackermann** concept: low speed favors 100% Ackermann (geometric); high speed with slip angles favors reduced/anti-Ackermann. AC models this via steering arm geometry.
- Add brief **Bump Steer** note: modeled in AC, emerges from steering rod geometry, visible via dev apps. Not adjustable but affects behavior.

Adjustable Parameters section:
- Add toe trade-off specifics: front toe-out increases turn-in response but reduces straight-line stability; rear toe-in universally used in competition (0.5-1.5mm total) for rear stability

Telemetry Diagnosis section:
- Add thermal gradient inner-to-outer as primary camber diagnostic (ideal ~5-10 deg C hotter inner than outer under load)
- Add steering angle vs lateral G scatter plot for Ackermann effects

### Phase E: Priority 9-10 Documents (Aero & Methodology)

**E1. Edit `aero_balance.md`** (Priority 9)

Physical Principles section:
- Add **AC's Aero Model** subsection: each element is an independent "wing" with its own CL, CD, AOA lookup tables, and ground height lookup tables (LUT_GH_CL, LUT_GH_CD). Elements do NOT interact with each other — lowering the splitter increases front downforce without affecting the rear diffuser. This is a significant simplification vs reality and vs ACC (which uses full aero maps with inter-element interaction).
- Add V-squared force scaling explicit statement and its diagnostic implication: compare balance in slow vs fast corners to isolate aero vs mechanical contribution.
- Add **Center of Pressure vs Center of Gravity** subsection: if CoP != CoG, downforce creates a pitch moment that changes with V-squared. Aero balance = front downforce / total downforce.
- Add **Aerodynamic Efficiency (L/D)** subsection: downforce-to-drag ratio. High L/D needed for low-drag circuits; low L/D acceptable for high-downforce circuits.
- Add note on yaw sensitivity modeled via YAW_CL_GAIN and YAW_CD_GAIN (linear approximation).
- Add note on DRS/dynamic controllers: AC models `[DYNAMIC_CONTROLLER]` for active aero.

Adjustable Parameters section:
- Add aero platform stability concept: maintaining consistent ride height under all conditions is critical because ride height changes alter aero balance. Springs, anti-dive, bump stops all contribute.

Telemetry Diagnosis section:
- Add balance vs speed plot as key diagnostic (overlay understeer gradient at different speed ranges)
- Add front/rear ride height under aero load

Cross-References section:
- Ensure references to suspension (ride height → platform), dampers (platform control), and braking (aero effect on bias) are present

**E2. Edit `setup_methodology.md`** (Priority 10)

Physical Principles section:
- Add acknowledgment of OVAT limitations: does not detect interaction effects between parameters. Mention simplified DOE (factorial designs) as alternative for advanced users.
- Add **Parameter Sensitivity Hierarchy** subsection: high sensitivity (ride height, spring rates, wing angle, tire pressures), medium (ARB stiffness, damper rates, diff settings, brake bias), low (camber fine-tuning, toe, individual gear ratios). Test high-sensitivity parameters first.
- Add **Interaction Effects** subsection: key interactions (spring↔damper, ride height↔aero, pressure↔camber, diff↔spring/ARB). Changing springs invalidates optimal damper settings.
- Add **Driver Adaptation as Confound** note: driver unconsciously adapts to setup changes (braking points, entry speed, throttle application). First laps on new setup unreliable. Recommend adaptation laps before timed comparison.

Adjustable Parameters section:
- Update priority order to more precise sequence: ride height/aero platform → pressures/temps base → gross balance (springs, ARBs) → damping → fine balance (diff, brake bias) → fine-tuning (camber, toe, final pressures)
- Replace "differential ramp angles" with "differential lock settings"
- Increase recommended lap count from 3-5 to 8-10 minimum per configuration; recommend median over mean for robustness to outliers

Telemetry Diagnosis section:
- Add A/B test protocol guidance: minimum laps, outlier removal, statistical comparison
- Add sensitivity plot concept (lap time vs parameter value)

### Phase F: Index Update and Validation

**F1. Update KNOWLEDGE_INDEX in `index.py`**

Add new tags to existing section entries where new content was added. See research.md R3 for the complete tag addition list per document.

Key additions:
- tyre_dynamics.md Physical Principles: `"brush model"`, `"pneumatic trail"`, `"self-aligning torque"`, `"relaxation length"`, `"camber thrust"`
- vehicle_balance_fundamentals.md Physical Principles: `"TLLTD"`, `"roll center"`, `"transient"`, `"steady state"`, `"weight transfer decomposition"`
- suspension_and_springs.md Physical Principles: `"wheel rate"`, `"anti-dive"`, `"anti-squat"`, `"roll center"`
- dampers.md Physical Principles: `"damping ratio"`, `"velocity domain"`, `"platform control"`
- drivetrain.md Physical Principles: replace `"power ramp"`, `"coast ramp"` with `"power lock"`, `"coast lock"`, `"lock percentage"`
- alignment.md Physical Principles: `"dynamic camber"`, `"camber thrust"`, `"ackermann"`
- aero_balance.md Physical Principles: `"center of pressure"`, `"lift to drag"`, `"efficiency"`
- telemetry_and_diagnosis.md Telemetry Diagnosis: `"g-g diagram"`, `"friction circle"`, `"reference lap"`
- setup_methodology.md Physical Principles: `"interaction effects"`, `"parameter sensitivity"`

**F2. Run Tests**

```bash
conda run -n ac-race-engineer pytest backend/tests/knowledge/ -v
```

All 48 tests must pass. If any fail, diagnose and fix (likely a section title typo or document structure issue).

**F3. Cross-Document Consistency Verification**

Grep across all 10 documents for:
- "ramp angle" — should only appear as "real-world ramp angles" context, never as AC parameter
- "springs govern.*transient rate" or similar — must be zero matches
- "spring rate" in suspension_and_springs.md — must be preceded or followed by wheel rate clarification
- "20-30 Hz" or "20–30 Hz" — must be zero matches (replaced with correct rates)
- "brake duct" in braking.md — must be accompanied by car-specific availability note
