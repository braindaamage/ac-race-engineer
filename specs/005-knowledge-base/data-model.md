# Data Model: Knowledge Base Module

**Branch**: `005-knowledge-base` | **Date**: 2026-03-04

## Entities

### KnowledgeFragment

The output unit returned by both retrieval functions. Immutable after creation.

| Field | Type | Description |
|-------|------|-------------|
| `source_file` | `str` | Filename of the source document (e.g., `vehicle_balance_fundamentals.md`) |
| `section_title` | `str` | H2 section heading matched (e.g., `Physical Principles`) |
| `content` | `str` | Full text content of the matched section |
| `tags` | `list[str]` | Keywords associated with this section from KNOWLEDGE_INDEX |

**Validation rules**:
- `source_file` must be non-empty
- `section_title` must be non-empty
- `content` can be empty (valid structure, no content yet)
- `tags` can be empty list (user documents not in index)

### KNOWLEDGE_INDEX (dict)

Static mapping from document filenames to section metadata. Built at module definition time.

```
{
    "vehicle_balance_fundamentals.md": {
        "Physical Principles": ["weight transfer", "understeer", "oversteer", "balance", "corner phase", "load", "gradient"],
        "Adjustable Parameters and Effects": ["spring rate", "anti-roll bar", "ride height", "weight distribution", "aero balance"],
        "Telemetry Diagnosis": ["understeer ratio", "slip angle", "yaw rate", "lateral g"],
        "Cross-References": ["suspension_and_springs", "alignment", "aero_balance"]
    },
    ...
}
```

Structure: `dict[str, dict[str, list[str]]]`
- Key: document filename
- Value: dict of section_title → list of tags

### SIGNAL_MAP (dict)

Static mapping from signal condition names to relevant (document, section) pairs.

```
{
    "high_understeer": [
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
        ("vehicle_balance_fundamentals.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("aero_balance.md", "Adjustable Parameters and Effects"),
    ],
    "tyre_temp_spread_high": [
        ("tyre_dynamics.md", "Telemetry Diagnosis"),
        ("tyre_dynamics.md", "Physical Principles"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
    ],
    ...
}
```

Structure: `dict[str, list[tuple[str, str]]]`
- Key: signal name
- Value: list of (document filename, section title) tuples

### Signal Detection Thresholds (constants)

Module-level constants used by signal detector functions.

| Constant | Type | Description |
|----------|------|-------------|
| `UNDERSTEER_THRESHOLD` | `float` | understeer_ratio above which "high_understeer" fires |
| `OVERSTEER_THRESHOLD` | `float` | understeer_ratio below which "high_oversteer" fires (negative) |
| `TEMP_SPREAD_THRESHOLD` | `float` | tyre temp_spread (°C) above which "tyre_temp_spread_high" fires |
| `TEMP_BALANCE_THRESHOLD` | `float` | front_rear_balance deviation triggering "tyre_temp_imbalance" |
| `LAP_TIME_SLOPE_THRESHOLD` | `float` | lap_time_slope (s/lap) above which "lap_time_degradation" fires |
| `SLIP_ANGLE_THRESHOLD` | `float` | slip angle average above which "high_slip_angle" fires |
| `CONSISTENCY_THRESHOLD` | `float` | lap_time_stddev_s above which "low_consistency" fires |

### Loaded Document Cache (internal)

Internal module-level cache populated on first use.

Structure: `dict[str, dict[str, str]]`
- Key: document filename
- Value: dict of section_title → section content text

## Relationships

```
AnalyzedSession ──(inspected by)──> Signal Detectors
Signal Detectors ──(produce)──> list[str] signal names
Signal names ──(lookup in)──> SIGNAL_MAP
SIGNAL_MAP entries ──(resolve via)──> Document Cache
Document Cache + KNOWLEDGE_INDEX ──(produce)──> list[KnowledgeFragment]

Query string ──(tokenized)──> keywords
Keywords ──(matched against)──> KNOWLEDGE_INDEX tags + Document Cache content
Matches ──(produce)──> list[KnowledgeFragment]
```

## Document File Layout

```
backend/ac_engineer/knowledge/
├── __init__.py              # Public API: get_knowledge_for_signals, search_knowledge
├── models.py                # KnowledgeFragment model
├── index.py                 # KNOWLEDGE_INDEX, SIGNAL_MAP constants
├── loader.py                # Document loading, parsing, validation, caching
├── signals.py               # Signal detector functions + thresholds
├── search.py                # Keyword search implementation
└── docs/
    ├── vehicle_balance_fundamentals.md
    ├── suspension_and_springs.md
    ├── dampers.md
    ├── alignment.md
    ├── aero_balance.md
    ├── braking.md
    ├── drivetrain.md
    ├── tyre_dynamics.md
    ├── telemetry_and_diagnosis.md
    ├── setup_methodology.md
    ├── car_template.md
    ├── track_template.md
    └── user/                # User-created documents (gitignored)
```
