# Implementation Plan: ACD File Reader

**Branch**: `021-acd-reader` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/021-acd-reader/spec.md`

## Summary

Implement a pure-computation Python module that reads and decrypts Assetto Corsa `data.acd` files. The module derives a decryption key from the car folder name using 8 arithmetic operations, XOR-decrypts the sequential binary archive, and returns all contained files as a `dict[str, bytes]` mapping. A single public function and a result dataclass form the entire API surface. Internal helpers handle key derivation, byte-level decryption, archive parsing, and readability detection (printable ASCII ratio >= 0.85 on first 512 bytes). The module is fully autonomous with zero external dependencies.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: None — Python standard library only
**Storage**: N/A — read-only file access, no persistence
**Testing**: pytest with `tmp_path` fixtures, no external filesystem side effects
**Target Platform**: Windows (primary), cross-platform compatible
**Project Type**: Library (autonomous subpackage within `backend/ac_engineer/`)
**Performance Goals**: Process a typical data.acd (10-30 files) in < 1 second
**Constraints**: Zero external dependencies, read-only operations, no unhandled exceptions
**Scale/Scope**: Single module (~200-300 LOC), single public function + result type

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Module validates archive integrity; corrupted/unreadable data is reported, never silently passed through |
| II. Car-Agnostic Design | PASS | Works with any car folder name — no hardcoded car logic. Key derivation uses the name generically |
| III. Setup File Autonomy | PASS | Read-only module; does not write setup files. Supports Phase 8.2 which will use extracted ranges for validation |
| IV. LLM as Interpreter | N/A | No LLM interaction in this module |
| V. Educational Explanations | N/A | No user-facing explanations in this module |
| VI. Incremental Changes | N/A | No setup modifications in this module |
| VII. Desktop App as Primary Interface | N/A | No UI in this module |
| VIII. API-First Design | PASS | Pure computation in `ac_engineer/` — no HTTP code, no framework imports |
| IX. Separation of Concerns | PASS | Lives in `ac_engineer/acd_reader/` (computation layer). No cross-layer imports |
| X. Desktop App Stack | N/A | No frontend in this module |
| XI. LLM Provider Abstraction | N/A | No LLM interaction |
| XII. Frontend Architecture | N/A | No frontend |

All applicable gates pass. No violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/021-acd-reader/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── public-api.md    # Public function signature and result type
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   └── acd_reader/
│       ├── __init__.py      # Public API: read_acd, AcdResult
│       └── reader.py        # All implementation: key derivation, decryption, parsing, readability check
└── tests/
    └── acd_reader/
        ├── conftest.py      # Fixtures: ACD archive builder, sample car names
        └── test_reader.py   # Tests for all public and edge-case behavior
```

**Structure Decision**: Single subpackage within the existing `backend/ac_engineer/` hierarchy. Follows the same pattern as `config/`, `storage/`, etc.: `__init__.py` with explicit `__all__` exports, implementation in a dedicated module. Tests follow `backend/tests/{module}/` convention with `conftest.py` for shared fixtures.
