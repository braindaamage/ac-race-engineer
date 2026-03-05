# Implementation Plan: Analysis Endpoints

**Branch**: `012-analysis-endpoints` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-analysis-endpoints/spec.md`

## Summary

Analysis Endpoints (Phase 6.3) connects the existing parser and analyzer pipelines (Phases 2+3) to the FastAPI backend. A processing endpoint wraps the full parse+analyze pipeline as a tracked background job with real-time progress, advancing session state from "discovered" to "analyzed" and caching results to disk. Seven synchronous metric query endpoints load from the cache to serve lap, corner, stint, comparison, and consistency data. The new `api/analysis/` package handles cache I/O, pipeline orchestration, and response serialization, while `api/routes/analysis.py` provides thin HTTP wrappers.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: FastAPI, Pydantic v2, pandas (for parser cache), httpx (test client)
**Storage**: SQLite (session state), JSON file cache (AnalyzedSession), Parquet + JSON (ParsedSession intermediate via existing parser cache)
**Testing**: pytest with `tmp_path` fixtures, httpx AsyncClient for endpoint tests, programmatic test data from existing analyzer conftest helpers
**Target Platform**: Windows 10/11 (primary), cross-platform compatible
**Project Type**: Desktop app backend (API server)
**Performance Goals**: Processing <10s for 20-lap session, metric queries <500ms from cache
**Constraints**: Single-user, local-only, one processing job per session at a time
**Scale/Scope**: Sessions with up to 50+ laps, multiple stints, dozens of corners

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Data Integrity First | PASS | Processing validates CSV + meta.json existence before running. Parser's built-in quality validation handles incomplete/inconsistent data. Processing fails with clear error on bad data — no guessing. |
| II. Car-Agnostic Design | PASS | No car-specific logic. Parser and analyzer are already car-agnostic. Cache format is generic. |
| III. Setup File Autonomy | N/A | This phase reads setup data from the parsed session cache but does not write setup files. |
| IV. LLM as Interpreter | N/A | No LLM interaction in this phase. All metrics are deterministic. |
| V. Educational Explanations | N/A | No setup recommendations in this phase. |
| VI. Incremental Changes | N/A | No setup changes in this phase. |
| VII. CLI-First MVP | PASS | All functionality exposed via HTTP endpoints, usable from CLI via curl. No GUI required. |
| VIII. API-First Design | PASS | All analysis logic lives in `ac_engineer.parser` and `ac_engineer.analyzer` as pure Python. The new `api/analysis/` modules handle only orchestration, caching, and serialization — no business logic. Routes are thin wrappers. |
| IX. Separation of Concerns | PASS | `ac_engineer/parser` and `ac_engineer/analyzer` remain untouched. `api/analysis/cache.py` handles serialization. `api/analysis/pipeline.py` orchestrates the job. `api/analysis/serializers.py` transforms data shapes. `api/routes/analysis.py` is HTTP-only. No reverse imports. |
| X. Desktop App Stack | N/A | No frontend in this phase. |
| XI. LLM Provider Abstraction | N/A | No LLM usage in this phase. |

**Post-design re-check**: All gates pass. The pipeline orchestration in `api/analysis/pipeline.py` calls `ac_engineer` functions — it does not contain analysis logic itself. Serializers convert existing Pydantic models to response shapes without re-computing metrics.

## Project Structure

### Documentation (this feature)

```text
specs/012-analysis-endpoints/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity models and cache format
├── quickstart.md        # Phase 1: dev setup guide
├── contracts/
│   └── analysis-api.md  # Phase 1: HTTP endpoint contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  api/
    analysis/
      __init__.py          # new: package init, public exports
      cache.py             # new: save/load AnalyzedSession JSON cache, get_cache_dir()
      pipeline.py          # new: run_processing_pipeline() — job callable with progress callbacks
      serializers.py       # new: AnalyzedSession → API response shapes (lap summaries, corner aggregates)
    routes/
      analysis.py          # new: POST /sessions/{id}/process + 7 metric GET endpoints
    main.py               # extend: register analysis router
  tests/
    api/
      test_analysis_cache.py        # new: cache save/load round-trip tests
      test_analysis_pipeline.py     # new: pipeline job tests with progress verification
      test_analysis_serializers.py  # new: serializer unit tests (corner aggregation, lap summaries)
      test_analysis_routes.py       # new: endpoint integration tests (all 8 endpoints + guard rails)
```

**Structure Decision**: New `api/analysis/` package follows the same pattern as `api/watcher/` — pure orchestration logic separate from HTTP routes. No modifications to `ac_engineer/parser`, `ac_engineer/analyzer`, `api/jobs`, or existing routes. Only `api/main.py` gets a one-line router registration addition.
