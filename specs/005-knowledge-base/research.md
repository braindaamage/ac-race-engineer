# Research: Knowledge Base Module

**Branch**: `005-knowledge-base` | **Date**: 2026-03-04

## R1: Document Structure and Parsing Strategy

**Decision**: Parse Markdown documents using regex on `## ` headings to extract sections. Each document has exactly 4 required H2 sections.

**Rationale**: The documents are authored with a known, controlled structure. A simple regex split on `^## ` lines is sufficient and avoids introducing a Markdown parser dependency. The 4 required sections are:
1. `## Physical Principles`
2. `## Adjustable Parameters and Effects`
3. `## Telemetry Diagnosis`
4. `## Cross-References`

**Alternatives considered**:
- `markdown` or `mistune` library: Adds external dependency for no benefit given the simple, controlled format.
- Line-by-line state machine: More code than regex, same result.

## R2: Signal Detection Approach

**Decision**: Define signal detector functions that inspect `AnalyzedSession` fields against threshold constants. Each detector returns a bool. A registry maps detector names to SIGNAL_MAP keys.

**Rationale**: The analyzer already computes all relevant metrics (understeer_ratio, temp_spread, lap_time_slope, etc.). Signal detection is threshold comparison — simple enough for standalone functions. Thresholds are module-level constants, easily tunable.

**Signal detectors planned** (keyed to AnalyzedSession fields):
| Signal Name | Source Field(s) | Condition |
|-------------|----------------|-----------|
| `high_understeer` | `CornerGrip.understeer_ratio` | Mean across flying lap corners > threshold |
| `high_oversteer` | `CornerGrip.understeer_ratio` | Mean across flying lap corners < negative threshold |
| `tyre_temp_spread_high` | `TyreMetrics.temp_spread` | Any wheel's spread > threshold |
| `tyre_temp_imbalance` | `TyreMetrics.front_rear_balance` | Absolute value > threshold |
| `lap_time_degradation` | `StintTrends.lap_time_slope` | Positive slope > threshold |
| `high_slip_angle` | `GripMetrics.slip_angle_avg` | Any wheel avg > threshold |
| `suspension_bottoming` | `SuspensionMetrics.travel_peak` | Any wheel peak near max |
| `low_consistency` | `ConsistencyMetrics.lap_time_stddev_s` | Stddev > threshold |
| `brake_balance_issue` | Corner entry understeer/oversteer pattern | Consistent entry-phase imbalance |
| `tyre_wear_rapid` | `StintTrends.tyre_temp_slope` | Positive slope > threshold |

**Alternatives considered**:
- ML-based anomaly detection: Violates zero-dependency constraint and over-engineers the problem.
- User-defined thresholds via config file: Premature — constants are sufficient and can be extracted to config later.

## R3: Keyword Search Implementation

**Decision**: Case-insensitive token matching. Tokenize query by splitting on whitespace and punctuation, then match tokens against (a) KNOWLEDGE_INDEX tags and (b) document section content. Rank by match count.

**Rationale**: The technical vocabulary in the documents is precise and consistent. Simple token matching works well for queries like "rear anti-roll bar oversteer" because the exact words appear in the documents. No stemming or fuzzy matching needed.

**Alternatives considered**:
- TF-IDF: Adds scipy dependency and complexity for marginal improvement on a 12-document corpus.
- Embedding-based search: Explicitly excluded by spec (no vector DB, no embeddings).
- Regex-based search: Unnecessary — token matching is sufficient and simpler.

## R4: Document Loading and Caching

**Decision**: Load all documents once at first use (lazy singleton). Parse into a dict of `{filename: {section_title: content}}`. Validation runs at load time. Cache in module-level variable.

**Rationale**: With only 12 documents, loading is fast (<100ms). A lazy singleton avoids paying the cost when the module is imported but not used. Re-loading is not needed since documents are static during a session.

**Alternatives considered**:
- Load on every call: Wasteful for repeated queries in a single engineer session.
- Eager load at import: Slows down module import even when knowledge is not needed.

## R5: User Template Discovery

**Decision**: User documents live in a `user/` subdirectory under `docs/`. At load time, scan both `docs/*.md` and `docs/user/*.md`. Templates are bundled in `docs/` with a `_template` suffix (e.g., `car_template.md`, `track_template.md`). User-created documents from templates go in `docs/user/`.

**Rationale**: Separating user docs from bundled docs prevents user files from being overwritten on updates and makes it clear which files are editable.

**Alternatives considered**:
- All in one directory: Risk of user files conflicting with bundled filenames.
- External directory (e.g., `data/knowledge/`): Breaks package self-containment; harder to distribute.

## R6: KnowledgeFragment Model Design

**Decision**: Simple Pydantic BaseModel with 4 fields: `source_file: str`, `section_title: str`, `content: str`, `tags: list[str]`.

**Rationale**: Matches spec requirement exactly. No additional fields needed. Tags come from KNOWLEDGE_INDEX for indexed documents, or are empty for user documents not in the index.

**Alternatives considered**:
- Add relevance_score field: Could be useful but spec doesn't require it and adds complexity to deduplication.
- Add signal_name field to track which signal triggered retrieval: Useful for debugging but not required by spec. Can be added later.
