# Public API Contract: Telemetry Analyzer

**Feature**: 004-telemetry-analyzer
**Date**: 2026-03-04

## Package Entry Point

```python
from ac_engineer.analyzer import analyze_session
from ac_engineer.analyzer import (
    AnalyzedSession,
    AnalyzedLap,
    LapMetrics,
    CornerMetrics,
    StintMetrics,
    StintComparison,
    ConsistencyMetrics,
)
```

## Primary Function

### `analyze_session(session: ParsedSession) -> AnalyzedSession`

Accepts a ParsedSession (from the parser) and returns an AnalyzedSession with all computed metrics.

**Guarantees**:
- Never modifies the input ParsedSession
- Never raises exceptions for valid ParsedSession input (degrades gracefully with None metrics)
- Deterministic: identical input → identical output
- No side effects (no I/O, no network, no LLM calls)

**Input contract**:
- `session` must be a valid `ParsedSession` instance (from `ac_engineer.parser`)
- `session.laps` may be empty (produces empty AnalyzedSession)
- Lap data may contain NaN values (handled gracefully)

**Output contract**:
- `AnalyzedSession.laps` has exactly `len(session.laps)` entries, in same order
- `AnalyzedSession.stints` has >= 1 entry if session has any laps
- `AnalyzedSession.stint_comparisons` has `len(stints) - 1` entries
- `AnalyzedSession.consistency` is None only if 0 flying laps

## Model Re-exports

All Pydantic model classes defined in `analyzer/models.py` are re-exported from `ac_engineer.analyzer`:

- `AnalyzedSession`, `AnalyzedLap`
- `LapMetrics`, `TimingMetrics`, `TyreMetrics`, `WheelTempZones`, `GripMetrics`, `DriverInputMetrics`, `SpeedMetrics`, `FuelMetrics`, `SuspensionMetrics`
- `CornerMetrics`, `CornerPerformance`, `CornerGrip`, `CornerTechnique`, `CornerLoading`
- `StintMetrics`, `AggregatedStintMetrics`, `StintTrends`
- `StintComparison`, `SetupParameterDelta`, `MetricDeltas`
- `ConsistencyMetrics`, `CornerConsistency`

## Dependency Direction

```
ac_engineer.analyzer imports from ac_engineer.parser.models (read-only)
ac_engineer.analyzer does NOT import from ac_engineer.parser internals
ac_engineer.parser does NOT import from ac_engineer.analyzer
```
