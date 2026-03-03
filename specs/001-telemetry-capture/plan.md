# Implementation Plan: Telemetry Capture App

**Branch**: `001-telemetry-capture` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-telemetry-capture/spec.md`

## Summary

Build a Python telemetry capture application that runs inside Assetto Corsa's embedded Python ~3.3 runtime as an in-game app. The app automatically records 76 telemetry channels at 20-30Hz to CSV files with JSON metadata sidecars, using a buffered write strategy for crash safety and zero frame-time impact. A hybrid data access approach combines `ac.getCarState()` (primary) with `sim_info.py` shared memory (secondary) to maximize channel coverage across all cars including mods.

## Technical Context

**Language/Version**: Python ~3.3.5 (AC's embedded runtime) for in-game code; Python 3.11+ (conda `ac-race-engineer` env) for tests and utilities
**Primary Dependencies**: `ac`, `acsys` (AC proprietary modules); Python stdlib only (`csv`, `json`, `os`, `time`, `configparser`, `math`, `collections`, `traceback`, `sys`, `io`, `struct`); `ctypes`/`mmap` for shared memory (optional)
**Storage**: CSV files (telemetry data), JSON sidecar files (session metadata), INI (app configuration)
**Testing**: pytest in conda env with mock `ac`/`acsys` modules; manual integration testing in AC
**Target Platform**: Windows (Assetto Corsa), AC's embedded Python ~3.3 runtime
**Project Type**: AC Python app (in-game plugin)
**Performance Goals**: Zero perceptible frame impact, 20-30Hz sampling, <5ms disk flush, return from acUpdate in <1ms on non-sampling frames
**Constraints**: No external packages, Python 3.3 syntax (no f-strings, no pathlib, no enum, no typing), no blocking I/O on main thread, bounded memory (~400KB buffer max), must work with vanilla and modded cars
**Scale/Scope**: Single user, sessions up to 60+ minutes, ~76 channels per sample, ~2-10 MB CSV per 30-minute session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|---|---|---|
| I. Data Integrity First | PASS | Captures raw data faithfully. Missing channels → NaN. No filtering at capture stage. Logs unavailable channels at session start. |
| II. Car-Agnostic Design | PASS | No hardcoded car logic. Dynamic channel reading with try/except. Every `ac.getCarState()` call wrapped for graceful failure. Works with vanilla and mods. |
| III. Setup File Autonomy | PASS | Read-only access to setup .ini at session start. Stores complete raw text in metadata. Does not modify setup files. |
| IV. LLM as Interpreter | N/A | No LLM integration in this feature. Pure data capture. |
| V. Educational Explanations | N/A | No user-facing explanations in this feature. |
| VI. Incremental Changes | N/A | No setup modifications in this feature. |
| VII. CLI-First MVP | PASS | This is a prerequisite for CLI analysis (Phase 2+). The in-game app captures data that the CLI will consume. |
| Dev Environment | PASS | AC app uses AC's Python ~3.3 (documented exception per constitution). Tests run in conda `ac-race-engineer` env. |

**Gate result**: PASS — no violations.

### Post-Design Re-check

| Principle | Status | Notes |
|---|---|---|
| II. Car-Agnostic Design | PASS | Channel definitions are data-driven (list of ChannelDefinition objects). No car-name checks anywhere. |
| I. Data Integrity | PASS | All 76 channels always present in CSV. Missing → empty cell (NaN). `channels_unavailable` list in metadata for transparency. |

**Post-design gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-telemetry-capture/
├── plan.md              # This file
├── research.md          # Phase 0: technical research decisions
├── data-model.md        # Phase 1: entity definitions and channel map
├── quickstart.md        # Phase 1: installation and usage guide
├── contracts/           # Phase 1: output format contracts
│   ├── csv-output.md    #   CSV telemetry format specification
│   ├── meta-json.md     #   Session metadata JSON schema
│   └── config-ini.md    #   App configuration format
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
ac_app/
└── ac_race_engineer/               # Distributable AC app folder
    ├── ac_race_engineer.py          # Entry point (acMain, acUpdate, acShutdown)
    ├── config.ini                   # Default configuration
    ├── sim_info.py                  # Shared memory wrapper (extended)
    ├── DLLs/                        # _ctypes.pyd (user-provided, not in repo)
    │   └── .gitkeep
    └── modules/                     # Core logic (pure functions, testable)
        ├── __init__.py
        ├── channels.py              # Channel definitions and telemetry reading
        ├── buffer.py                # In-memory sample buffer management
        ├── writer.py                # CSV header/row writing and JSON metadata
        ├── config_reader.py         # config.ini parsing with defaults/validation
        ├── session.py               # Session lifecycle state machine
        ├── setup_reader.py          # Setup .ini file discovery and reading
        ├── sanitize.py              # Filename sanitization
        └── status.py                # UI status indicator (color/text updates)

tests/
└── telemetry_capture/               # pytest tests (run in conda env)
    ├── conftest.py                  # Fixtures, path setup, mock injection
    ├── mocks/                       # Mock modules for AC's proprietary APIs
    │   ├── __init__.py
    │   ├── ac.py                    # Mock ac module
    │   └── acsys.py                 # Mock acsys module with CS constants
    └── unit/
        ├── test_buffer.py           # Buffer append, flush trigger, clear
        ├── test_writer.py           # CSV write, JSON write, file naming
        ├── test_channels.py         # Channel reading, NaN fallback
        ├── test_config_reader.py    # Config parsing, defaults, validation
        ├── test_session.py          # State machine transitions
        ├── test_setup_reader.py     # Setup discovery, file reading
        └── test_sanitize.py         # Filename sanitization rules
```

**Structure Decision**: The AC app lives in `ac_app/ac_race_engineer/` as a self-contained, distributable folder. Users copy this entire folder into AC's `apps/python/` directory with no build step. Core logic in `modules/` is written as pure functions (no `ac`/`acsys` imports) so they can be tested via pytest in the conda environment. The entry point `ac_race_engineer.py` is the only file that imports `ac`/`acsys` and bridges between AC's lifecycle callbacks and the pure logic modules. Tests live in `tests/telemetry_capture/` and import modules from `ac_app/ac_race_engineer/modules/` via path manipulation in `conftest.py`.

## Complexity Tracking

> No constitution violations detected. This section is empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
