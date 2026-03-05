# Feature Specification: Refine Vehicle Dynamics Knowledge Base

**Feature Branch**: `009-refine-knowledge-docs`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Refine the vehicle dynamics knowledge base documents used as LLM context in the AC Race Engineer system."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct Tire Model References for Accurate Recommendations (Priority: P1)

A driver asks the AI engineer about tyre grip behavior. The specialist agent retrieves knowledge from `tyre_dynamics.md` and reasons about how the tyre generates force. Because the document correctly describes AC's brush-based tire model (not Pacejka), the agent's explanation and any setup recommendations are grounded in how the simulation actually works. The driver receives advice that matches what they observe in-game rather than advice based on a different tire model's characteristics.

**Why this priority**: The tire model is the foundational physics layer. Every other document references tyre behavior. If the tire model description is wrong, all downstream reasoning about balance, suspension, alignment, and braking inherits that error. This is the single highest-impact correction.

**Independent Test**: Can be verified by reading the refined `tyre_dynamics.md` and confirming zero Pacejka/Magic Formula references remain, replaced with brush model description. Additionally, the document must include tire load sensitivity, pneumatic trail/SAT, and relaxation length sections. All 48 existing knowledge base tests must continue passing.

**Acceptance Scenarios**:

1. **Given** the knowledge base contains `tyre_dynamics.md`, **When** a user or agent searches for tire model information, **Then** all references describe AC's brush-based model with bristle deformation, adhesion/sliding regions, and Coulomb friction — with no mention of Pacejka coefficients (B, C, D, E) as AC's model.
2. **Given** a session with high slip angles detected, **When** the tyre specialist agent loads tyre knowledge, **Then** the retrieved content explains tire load sensitivity as the mechanism connecting vertical load to lateral grip (concave Fy-Fz relationship), enabling the agent to reason about why weight transfer affects balance.
3. **Given** a driver reports "the steering goes light before I lose grip", **When** the agent searches for relevant knowledge, **Then** it finds a section on pneumatic trail and self-aligning torque explaining this as the trail approaching zero near the adhesion limit.

---

### User Story 2 - Correct Springs/Dampers Causal Attribution for Balance Tuning (Priority: P1)

A driver reports mid-corner understeer that appears during quick direction changes. The balance specialist agent retrieves knowledge from `vehicle_balance_fundamentals.md` and `suspension_and_springs.md`. Because these documents correctly attribute load transfer *magnitude and distribution* to springs/ARBs and load transfer *speed* to dampers, the agent correctly distinguishes between a steady-state balance problem (springs/ARBs) and a transient balance problem (dampers). The driver receives targeted advice rather than a confused mix of spring and damper changes.

**Why this priority**: This springs-vs-dampers causal inversion appears across multiple documents and directly causes incorrect setup recommendations. A driver with a transient problem would be told to change springs (wrong lever) instead of dampers (right lever), wasting their time and potentially making the problem worse.

**Independent Test**: Can be verified by searching all 10 documents for any claim that springs control "speed" or "rate" of weight transfer. Every such instance must be corrected to: springs/ARBs determine magnitude and distribution of steady-state lateral load transfer; dampers control the rate/speed at which that transfer occurs.

**Acceptance Scenarios**:

1. **Given** the knowledge base documents `vehicle_balance_fundamentals.md`, `suspension_and_springs.md`, and `dampers.md`, **When** the content is reviewed for causal attribution of load transfer, **Then** all three documents consistently state: springs/ARBs control steady-state load transfer distribution (LLTD); dampers control the transient rate of load transfer.
2. **Given** a session where oversteer appears only during transitions (not at steady-state mid-corner), **When** the balance agent retrieves knowledge, **Then** it finds content that clearly separates transient vs steady-state balance mechanisms, pointing to dampers for transient issues and springs/ARBs for steady-state issues.

---

### User Story 3 - Correct AC-Specific Parameter Names and Availability (Priority: P1)

A driver asks for help with their differential settings on a GT3 car. The specialist agent retrieves knowledge from `drivetrain.md`. Because the document correctly describes AC's lock percentage model (POWER 0.0-1.0, COAST 0.0-1.0, PRELOAD in Nm) rather than ramp angles, and correctly notes which parameters are available on which car types, the agent makes recommendations using terms and values the driver can actually find and adjust in their setup screen.

**Why this priority**: If the knowledge base uses wrong parameter names (ramp angles instead of lock percentages) or presents non-universal parameters as always available (brake ducts on all cars), the agent will recommend changes the driver cannot make, eroding trust in the system.

**Independent Test**: Can be verified by reviewing each document for AC-specific parameter names and availability notes. `drivetrain.md` must use lock percentages; `braking.md` must note that brake ducts, pad compounds, and engine brake are car-specific; `suspension_and_springs.md` must clarify that SPRING_RATE values in AC represent wheel rates.

**Acceptance Scenarios**:

1. **Given** `drivetrain.md` in the knowledge base, **When** differential parameters are described, **Then** the document uses AC's actual parameter names (POWER, COAST as 0.0-1.0 lock percentages; PRELOAD in Nm) and does not reference ramp angles as AC parameters.
2. **Given** `braking.md` in the knowledge base, **When** braking parameters are described, **Then** brake ducts, pad compounds, and engine brake are noted as available only on specific cars (not universal), with guidance on how to handle cars that lack these options.
3. **Given** `suspension_and_springs.md` in the knowledge base, **When** spring rate parameters are described, **Then** the document explicitly states that AC's SPRING_RATE values and in-game setup values represent wheel rate (stiffness at the wheel), not spring rate at the physical spring.

---

### User Story 4 - Complete Telemetry Diagnosis Reference (Priority: P2)

A driver uploads a session for analysis. The system detects multiple signals (high understeer, tyre temp spread, brake balance issue). The specialist agents retrieve diagnostic guidance from `telemetry_and_diagnosis.md` and the relevant domain documents. Because the telemetry document correctly describes the available tools, realistic capture rates (30-200 Hz, not 20-30 Hz), and includes systematic diagnostic techniques (G-G diagrams, reference lap methodology, symptom-cause hypothesis generation), the agents produce well-structured analysis rather than superficial observations.

**Why this priority**: The telemetry document is the transversal reference that guides how all other domain knowledge is applied to actual data. Incorrect sample rates, missing diagnostic techniques, and a prescriptive symptom-cause table (instead of hypothesis-generating) reduce the quality of every analysis.

**Independent Test**: Can be verified by reading `telemetry_and_diagnosis.md` and confirming: correct capture rate information (physics ~333 Hz, logging 30-200 Hz), G-G diagram methodology present, reference lap methodology present, symptom-cause table reframed as hypothesis generator.

**Acceptance Scenarios**:

1. **Given** `telemetry_and_diagnosis.md` in the knowledge base, **When** sample rate information is referenced, **Then** the document states AC's internal physics runs at ~333 Hz and telemetry capture rates are 30-200 Hz depending on the tool, with no claims of 20-30 Hz as the standard.
2. **Given** a driver's session with understeer detected, **When** agents retrieve diagnostic methodology, **Then** the knowledge base includes G-G diagram analysis and reference lap comparison as diagnostic techniques alongside the symptom-cause table.

---

### User Story 5 - Content Gaps Filled for Key Mechanisms (Priority: P2)

A driver's session shows different balance characteristics in slow corners vs fast corners. The specialist agents retrieve knowledge that includes weight transfer decomposition (geometric, elastic, unsprung mass components), the relationship between ride height and roll center position, aero balance scaling with velocity squared, and dynamic camber effects. Because these mechanisms are documented, the agents can reason about *why* balance changes with speed and corner type, producing nuanced recommendations (e.g., "your slow-corner understeer is mechanical — try softening front ARB; your fast-corner understeer is aerodynamic — try increasing front wing").

**Why this priority**: Without these mechanisms documented, the LLM can only give generic balance advice. With them, it can distinguish mechanical from aerodynamic effects, steady-state from transient problems, and geometric from elastic contributions — dramatically improving recommendation specificity.

**Independent Test**: Can be verified by confirming the presence of: weight transfer decomposition in `vehicle_balance_fundamentals.md`, ride height to roll center relationship in `suspension_and_springs.md`, V-squared scaling and CoP vs CoG in `aero_balance.md`, dynamic camber in `alignment.md`, velocity domains in `dampers.md`.

**Acceptance Scenarios**:

1. **Given** `vehicle_balance_fundamentals.md`, **When** weight transfer is explained, **Then** the document includes the three-component decomposition (geometric via roll center, elastic via springs/ARBs, unsprung mass) and explains TLLTD as the unifying metric.
2. **Given** `aero_balance.md`, **When** aerodynamic effects are explained, **Then** the document describes AC's independent wing-element model (no inter-element interaction), V-squared force scaling, and Center of Pressure vs Center of Gravity concept.
3. **Given** `dampers.md`, **When** damper behavior is explained, **Then** the document includes velocity domain framework (low-speed body control, high-speed bump absorption) and AC's bilineal damping model with actual parameter names.

---

### User Story 6 - Cross-Document Consistency (Priority: P3)

A driver's session triggers signals that cause multiple specialist agents to retrieve overlapping knowledge from different documents. Because all documents use consistent terminology — the same tire model description, the same causal attributions, the same parameter names — the agents produce coherent, non-contradictory recommendations even when working from different source documents.

**Why this priority**: Contradictions between documents (e.g., one saying springs control transfer speed, another saying dampers do) cause the LLM to produce inconsistent or hedging recommendations. Cross-document consistency is the quality floor for the entire knowledge base.

**Independent Test**: Can be verified by searching across all 10 documents for key terms (tire model, load transfer speed, spring rate/wheel rate, lock percentage/ramp angle, sample rate) and confirming consistent usage everywhere.

**Acceptance Scenarios**:

1. **Given** all 10 knowledge base documents, **When** the tire model is referenced in any document, **Then** it is consistently described as a brush-based model (never Pacejka/Magic Formula as AC's model).
2. **Given** all 10 knowledge base documents, **When** load transfer causation is discussed, **Then** springs/ARBs are consistently attributed to steady-state distribution and dampers to transient rate, with no contradictions.
3. **Given** all 10 knowledge base documents, **When** AC-specific parameters are mentioned, **Then** correct names and availability caveats are used consistently (lock percentages not ramp angles, wheel rates not spring rates, car-specific parameters noted as such).

---

### Edge Cases

- What happens if a section title is changed during refinement? The KNOWLEDGE_INDEX in `index.py` must be updated to match, or the loader and search will fail to find the section.
- What happens if significantly new content is added that changes the scope of a section? The tags in KNOWLEDGE_INDEX should be expanded to include new concepts so that signal-based and query-based retrieval can find the new content.
- What happens if a document's corrections conflict with the audit report's recommendations? The audit report's factual corrections take precedence; content decisions (depth, examples, phrasing) follow the existing document style.
- What happens if a correction in one document creates an inconsistency with another document that hasn't been refined yet? All 10 documents must be refined, and cross-document consistency must be verified as a final step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All 10 knowledge base documents MUST be refined with corrections from `docs/AUDIT_REPORT.md` applied, in the priority order defined in that report
- **FR-002**: Every document MUST preserve the exact 4-section structure: Physical Principles / Adjustable Parameters and Effects / Telemetry Diagnosis / Cross-References
- **FR-003**: `tyre_dynamics.md` MUST replace all Pacejka/Magic Formula references with AC's brush-based tire model description (bristle deformation, adhesion/sliding regions, Coulomb friction)
- **FR-004**: `tyre_dynamics.md` MUST include new content on tire load sensitivity (with conceptual numeric example), pneumatic trail and self-aligning torque, relaxation length, camber thrust, and combined slip
- **FR-005**: `vehicle_balance_fundamentals.md` MUST correct the springs-to-transfer-speed attribution: springs/ARBs determine steady-state LLTD magnitude and distribution; dampers control the rate of transfer
- **FR-006**: `vehicle_balance_fundamentals.md` MUST include weight transfer decomposition (geometric, elastic, unsprung mass), TLLTD concept, and separation of transient vs steady-state balance
- **FR-007**: `suspension_and_springs.md` MUST explicitly state that AC's SPRING_RATE parameter and in-game setup values represent wheel rate, not spring rate
- **FR-008**: `suspension_and_springs.md` MUST include natural frequency reference table by vehicle category, ride height to roll center relationship, and bump stops as active tuning elements
- **FR-009**: `dampers.md` MUST document AC's bilineal damping model with actual parameter names (DAMP_BUMP, DAMP_FAST_BUMP, thresholds, etc.), velocity domain framework, target damping ratios, and rebound:compression ratio guidance
- **FR-010**: `alignment.md` MUST clarify which parameters are user-adjustable (camber, toe, sometimes caster) versus emergent geometry properties (KPI, scrub radius, Ackermann), and include dynamic camber content
- **FR-011**: `aero_balance.md` MUST describe AC's independent wing-element aero model (no inter-element interaction), V-squared scaling, Center of Pressure vs Center of Gravity, and L/D efficiency ratio
- **FR-012**: `braking.md` MUST note that brake ducts, pad compounds, engine brake, and brake fade are car-specific in AC (not universal), and include brake bias ideal calculation and deceleration reference values
- **FR-013**: `drivetrain.md` MUST use AC's actual parameter terminology (lock percentages 0.0-1.0 for POWER/COAST, PRELOAD in Nm) instead of ramp angles, and clearly separate preload from lock percentage behavior
- **FR-014**: `telemetry_and_diagnosis.md` MUST correct sample rate to: physics ~333 Hz internal, logging 30-200 Hz by tool; include G-G diagram methodology, reference lap comparison, and reframe symptom-cause table as hypothesis generator
- **FR-015**: `setup_methodology.md` MUST acknowledge OVAT limitations (no interaction detection), increase recommended lap count to 8-10 minimum, include parameter sensitivity hierarchy, and note driver adaptation as a confound
- **FR-016**: All 10 documents MUST use consistent terminology for shared concepts (tire model, load transfer causation, AC parameter names, telemetry rates)
- **FR-017**: The KNOWLEDGE_INDEX in `index.py` MUST be updated if section content scope changes significantly enough that existing tags no longer adequately represent the section's content for retrieval
- **FR-018**: The 3-layer content approach within each section MUST be maintained: physics fundamentals, then metric interpretation, then setup levers
- **FR-019**: All existing 48 knowledge base tests MUST continue passing after refinement (document structure, loader, search functionality unbroken)
- **FR-020**: Content within each section MUST follow the existing document style (prose paragraphs with bold subheadings, not bullet-heavy or textbook-dense)

### Key Entities

- **Knowledge Document**: A markdown file in the knowledge base with the mandatory 4-section structure, consumed by specialist agents for LLM reasoning context. 10 documents total covering vehicle dynamics domains.
- **KNOWLEDGE_INDEX**: A mapping from document filename to section titles to retrieval tags. Used by the search system to find relevant content for detected telemetry signals and agent queries.
- **SIGNAL_MAP**: A mapping from detected telemetry signals to specific (document, section) tuples. Determines which knowledge fragments are automatically pre-loaded when a signal is detected.
- **Audit Report**: The source of truth for required corrections (`docs/AUDIT_REPORT.md`), containing prioritized findings per document with specific error descriptions and recommended corrections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero Pacejka/Magic Formula references remain in any knowledge base document when searched across all 10 files (replaced with brush model descriptions)
- **SC-002**: Zero instances of springs being attributed as controlling the "speed" or "rate" of weight transfer across all 10 documents
- **SC-003**: 100% of AC-specific parameter names are accurate: lock percentages (not ramp angles) in drivetrain, wheel rates (not spring rates) in suspension, car-specific availability noted for brake ducts/pad compounds/engine brake/brake fade
- **SC-004**: All 10 documents maintain the exact 4-section structure (Physical Principles / Adjustable Parameters and Effects / Telemetry Diagnosis / Cross-References)
- **SC-005**: All 48 existing knowledge base tests pass without modification (document loading, parsing, search, and signal mapping unbroken)
- **SC-006**: Every factual correction identified in `docs/AUDIT_REPORT.md` is addressed in the corresponding document (traceable 1:1 from audit finding to document change)
- **SC-007**: Cross-document consistency verified: searching for key shared concepts (tire model, load transfer causation, parameter names, sample rates) returns consistent information regardless of which document is retrieved
- **SC-008**: KNOWLEDGE_INDEX tags updated to reflect any new content areas added to documents, ensuring the search system can retrieve newly added knowledge (e.g., tire load sensitivity, pneumatic trail, weight transfer decomposition)

## Assumptions

- The audit report (`docs/AUDIT_REPORT.md`) is technically accurate and its factual corrections are authoritative. Content depth and phrasing decisions not dictated by the audit follow the existing document style.
- The 4-section structure is load-bearing for the knowledge base loader and search system — changing section titles would require KNOWLEDGE_INDEX updates and potentially code changes. Section titles will not be changed.
- The SIGNAL_MAP does not need updating since no new signals are being added — only the content behind existing mappings is being refined.
- Template documents (`car_template.md`, `track_template.md`) are out of scope for this refinement as they are structural templates, not vehicle dynamics content.
- The user-created docs directory (`docs/user/`) is out of scope.
