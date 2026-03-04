# Feature Specification: Knowledge Base Module

**Feature Branch**: `005-knowledge-base`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Build the Knowledge Base module for the AC Race Engineer AI system (Phase 4) — a self-contained technical reference library of vehicle dynamics knowledge, with domain documents in Markdown and deterministic retrieval functions that map analyzed session signals to relevant content."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Signal-Based Knowledge Retrieval (Priority: P1)

After a telemetry session is analyzed, the system automatically identifies problematic conditions (e.g., understeer in corners, excessive tyre temperature spread, lap time degradation over a stint) and retrieves the relevant vehicle dynamics knowledge that explains the physics behind those conditions, what setup parameters affect them, and how to diagnose them from telemetry. This pre-loaded knowledge will later be injected into the AI engineer's context so it can ground its setup recommendations in real vehicle dynamics principles.

**Why this priority**: This is the core value of the knowledge base — without signal-based retrieval, the AI engineer would operate without domain grounding and could produce incorrect or generic advice.

**Independent Test**: Can be fully tested by constructing a mock AnalyzedSession with known signal patterns (e.g., high understeer_ratio on multiple corners) and verifying that the retrieval function returns fragments from the correct domain documents (e.g., vehicle_balance_fundamentals, alignment).

**Acceptance Scenarios**:

1. **Given** an AnalyzedSession where multiple corners show understeer_ratio > 1.2, **When** the system retrieves knowledge for detected signals, **Then** it returns fragments from documents covering vehicle_balance_fundamentals, suspension_and_springs, and alignment, each containing relevant physical principles and adjustable parameters.
2. **Given** an AnalyzedSession where tyre temp_spread exceeds a threshold on specific wheels, **When** the system retrieves knowledge for detected signals, **Then** it returns fragments covering tyre_dynamics, alignment, and suspension_and_springs.
3. **Given** an AnalyzedSession where stint trends show positive lap_time_slope (degradation), **When** the system retrieves knowledge for detected signals, **Then** it returns fragments covering tyre_dynamics, vehicle_balance_fundamentals, and setup_methodology.
4. **Given** an AnalyzedSession with no problematic signals detected (all metrics within normal ranges), **When** the system retrieves knowledge, **Then** it returns an empty or minimal set of fragments.

---

### User Story 2 - Keyword Search for Knowledge (Priority: P2)

A downstream consumer (the AI engineer agent or a developer during debugging) can search the knowledge base with a free-text query like "rear anti-roll bar oversteer" and get back relevant fragments. This supports ad-hoc lookups when the AI agent needs to explore a topic beyond what signal-based retrieval provided, or when a user asks a specific question about vehicle dynamics.

**Why this priority**: Keyword search complements signal-based retrieval by enabling flexible, on-demand lookups. It is simpler to implement than signal mapping but less automated.

**Independent Test**: Can be fully tested by calling the search function with known queries and verifying that results come from the expected documents and sections.

**Acceptance Scenarios**:

1. **Given** the knowledge base is loaded, **When** searching for "rear anti-roll bar oversteer", **Then** at least one fragment is returned from the suspension_and_springs or vehicle_balance_fundamentals document containing content about rear anti-roll bar effects on oversteer.
2. **Given** the knowledge base is loaded, **When** searching for "camber tyre temperature", **Then** fragments are returned covering camber angle effects on tyre contact patch and temperature distribution.
3. **Given** the knowledge base is loaded, **When** searching for a nonsense query like "xyzzy foobar", **Then** an empty list of fragments is returned.
4. **Given** the knowledge base is loaded, **When** searching for "brake bias", **Then** fragments are returned from the braking document, not from unrelated documents.

---

### User Story 3 - Document Structure Validation (Priority: P3)

All knowledge documents follow a consistent 4-section structure (physical principles, adjustable parameters and effects, telemetry diagnosis, cross-references) so that consumers can rely on predictable content organization. The system validates document structure at load time, and users can add or edit documents (including custom templates for car-specific or track-specific notes) knowing that structural consistency will be enforced.

**Why this priority**: Structural consistency is what makes the knowledge base reliable and extensible. Without it, retrieval functions cannot assume where to find specific types of content, and user-authored documents might break the system.

**Independent Test**: Can be fully tested by loading all bundled documents and templates, verifying each has the required sections, and testing that a malformed document is detected and reported.

**Acceptance Scenarios**:

1. **Given** all 10 bundled domain documents, **When** the system validates their structure at load time, **Then** all 10 pass validation with the required 4-section structure.
2. **Given** the 2 editable templates, **When** the system validates them, **Then** both pass structure validation.
3. **Given** a user-authored document missing the "Telemetry Diagnosis" section, **When** the system validates it, **Then** it reports the specific missing section and the document is excluded from retrieval or flagged with a warning.

---

### User Story 4 - User-Editable Templates (Priority: P4)

Users can create their own knowledge documents using provided templates — one for car-specific notes (e.g., "The Lotus 49 has no aero, so all grip is mechanical") and one for track-specific notes (e.g., "Monza T1 needs late braking and strong rear stability"). These user documents are indexed alongside the bundled domain documents and appear in both signal-based and keyword retrieval results.

**Why this priority**: Extensibility by users is valuable but not critical for initial functionality. The AI engineer can work with just the bundled documents.

**Independent Test**: Can be tested by placing a filled-in template document in the knowledge directory, loading the knowledge base, and verifying the user document appears in search results.

**Acceptance Scenarios**:

1. **Given** a user fills in the car-specific template with notes about a particular car, **When** the knowledge base is loaded, **Then** that document is indexed and its content appears in keyword search results.
2. **Given** a user fills in the track-specific template, **When** searching for content related to that track, **Then** fragments from the user document are returned alongside bundled document fragments.

---

### Edge Cases

- What happens when a knowledge document has valid structure but empty section content? The system should index it but return fragments with empty content (the consumer decides whether to use them).
- What happens when an AnalyzedSession has None/missing metrics (e.g., no fuel data, no corner data)? Signal detection must handle optional fields gracefully and only look for signals in available data.
- What happens when multiple signals fire simultaneously (e.g., understeer + high tyre temps + lap degradation)? The system should return the union of all relevant fragments, deduplicated by source_file + section_title.
- What happens when the knowledge documents directory doesn't exist or is empty? The system should return empty results without crashing.
- What happens when a search query contains only stop words or punctuation? The system should return empty results.

## Requirements *(mandatory)*

### Functional Requirements

#### Domain Documents

- **FR-001**: The module MUST include 10 domain knowledge documents covering the following vehicle dynamics topics: (1) vehicle_balance_fundamentals — weight transfer, understeer/oversteer gradient, balance by corner phase, (2) suspension_and_springs — spring rates, ride height (mechanical effects), ARBs, roll stiffness distribution, (3) dampers — slow/fast bump & rebound, damper velocity histograms, transient load transfer, (4) alignment — camber, toe, caster; static effects on contact patch and tyre temperature distribution, (5) aero_balance — downforce, drag, front/rear aero balance, ride height sensitivity, (6) braking — brake bias, engine braking, thermal management, trail braking, (7) drivetrain — differential types (LSD, preload, ramp angles), gear ratios, final drive, (8) tyre_dynamics — slip angle, traction circle, thermal model, pressure effects, wear, (9) telemetry_and_diagnosis — reading telemetry channels, driver input analysis, symptom-to-cause diagnosis table, (10) setup_methodology — baseline process, one-variable principle, session planning, change validation.
- **FR-002**: Each document MUST follow a 4-section structure: "Physical Principles" (theory of how the system works), "Adjustable Parameters and Effects" (what can be changed and what happens), "Telemetry Diagnosis" (how to spot issues in data), "Cross-References" (links to related documents/topics).
- **FR-003**: All document content MUST be car-agnostic — describing general vehicle dynamics principles, not specific to any car or mod. No decision logic (e.g., "if understeer, increase front ARB") — only informational content.
- **FR-004**: The module MUST include 2 editable user templates: one for car-specific notes and one for track-specific notes, both following the same 4-section structure.
- **FR-005**: Documents MUST be stored as Markdown files in a dedicated directory within the knowledge module.

#### Retrieval Index

- **FR-006**: The module MUST define a KNOWLEDGE_INDEX — a mapping from document filenames to their section headings and associated tags/keywords.
- **FR-007**: The module MUST define a SIGNAL_MAP — a mapping from detectable session conditions (signal names) to lists of relevant (document, section) pairs.
- **FR-008**: Signal conditions in SIGNAL_MAP MUST correspond to metrics available in the AnalyzedSession output model (e.g., understeer_ratio, tyre temp_spread, lap_time_slope, slip_angle averages, suspension_travel ranges).
- **FR-009**: Both KNOWLEDGE_INDEX and SIGNAL_MAP MUST be plain Python dictionaries with no external dependencies (no vector database, no embeddings, no ML models).

#### Retrieval Functions

- **FR-010**: The module MUST provide a `get_knowledge_for_signals(session: AnalyzedSession)` function that: (a) inspects the session for detectable conditions using threshold-based signal detection, (b) maps detected signals to relevant document sections via SIGNAL_MAP, (c) loads and returns matching content as KnowledgeFragment objects.
- **FR-011**: The module MUST provide a `search_knowledge(query: str)` function that: (a) tokenizes the query into keywords, (b) matches keywords against document content and index tags, (c) returns matching fragments ranked by relevance (number of keyword matches).
- **FR-012**: Both retrieval functions MUST return lists of KnowledgeFragment objects containing: source_file (document filename), section_title (matched section heading), content (full section text), and tags (list of associated keywords).
- **FR-013**: Results from `get_knowledge_for_signals` MUST be deduplicated — if multiple signals point to the same (document, section) pair, it appears only once in the result.

#### Validation

- **FR-014**: The module MUST validate document structure at load time, checking that each Markdown file contains all 4 required section headings.
- **FR-015**: Documents that fail validation MUST be reported (which file, which sections are missing) and excluded from retrieval results.

#### Integration Constraints

- **FR-016**: The module MUST NOT import from `api/` or any HTTP framework.
- **FR-017**: The module MUST have zero external dependencies beyond the project's existing stack (pydantic, standard library). No embeddings libraries, no vector stores, no NLP toolkits.
- **FR-018**: The module MUST be fully testable using mock fixtures — no real AnalyzedSession or real telemetry files required for tests.

### Key Entities

- **KnowledgeFragment**: A retrieved piece of knowledge — contains source file, section title, section content, and tags. Returned by both retrieval functions.
- **KNOWLEDGE_INDEX**: A dictionary mapping each document filename to its sections and their associated tags. Used for keyword matching.
- **SIGNAL_MAP**: A dictionary mapping signal condition names (e.g., "high_understeer", "tyre_temp_spread_excessive", "lap_time_degradation") to lists of (document, section) references. Used for signal-based retrieval.
- **Domain Document**: A Markdown file following the 4-section structure, containing vehicle dynamics knowledge about a specific topic.
- **User Template**: An editable Markdown file with the 4-section structure pre-filled with guidance, for users to add car-specific or track-specific notes.

## Assumptions

- Signal detection thresholds (e.g., understeer_ratio > 1.2 means "high understeer") will be defined as constants within the module. These can be tuned later without changing the retrieval architecture.
- The knowledge documents directory will be located within the `backend/ac_engineer/knowledge/` package, bundled with the module rather than in a separate data directory.
- User-authored documents (from templates) will be stored in the same directory or a subdirectory, and discovered automatically at load time.
- Document content will be written in English.
- The keyword search is simple token matching (case-insensitive, whitespace-split), not fuzzy matching or stemming. This is sufficient for the structured, technical vocabulary in the documents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `get_knowledge_for_signals` returns at least one relevant fragment for each of the three core signal conditions: understeer, tyre temperature spread, and lap time degradation — verified with mock session data.
- **SC-002**: `search_knowledge("rear anti-roll bar oversteer")` returns at least one fragment from the suspension_and_springs or vehicle_balance_fundamentals document.
- **SC-003**: All 10 domain documents and 2 templates pass the 4-section structure validation at module load time.
- **SC-004**: The complete test suite passes with zero external dependencies beyond pydantic and the Python standard library.
- **SC-005**: Signal-based retrieval returns no duplicate fragments when multiple signals point to the same document section.
- **SC-006**: Keyword search returns an empty list for queries with no matching content.
- **SC-007**: The module loads and validates all documents in under 1 second on a standard machine.
