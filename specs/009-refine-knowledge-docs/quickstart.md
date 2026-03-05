# Quickstart: Refine Knowledge Base Documents

**Branch**: `009-refine-knowledge-docs` | **Date**: 2026-03-05

## What This Feature Does

Corrects factual errors, fills content gaps, and ensures AC-specific accuracy across the 10 vehicle dynamics knowledge base documents that serve as LLM reasoning context for the AI race engineer's specialist agents.

## Key Files

- **Documents to edit**: `backend/ac_engineer/knowledge/docs/*.md` (10 domain documents)
- **Index to update**: `backend/ac_engineer/knowledge/index.py` (KNOWLEDGE_INDEX tags)
- **Audit source**: `docs/AUDIT_REPORT.md` (corrections reference)
- **Loader (read-only)**: `backend/ac_engineer/knowledge/loader.py` (validation logic)
- **Tests (must pass)**: `backend/tests/knowledge/` (48 tests)

## How to Validate

```bash
# Run knowledge base tests (48 tests)
conda run -n ac-race-engineer pytest backend/tests/knowledge/ -v

# Quick structural check — all docs must load
conda run -n ac-race-engineer python -c "from ac_engineer.knowledge.loader import load_all_documents; docs = load_all_documents(); print(f'{len(docs)} docs loaded'); assert len(docs) >= 12"

# Verify no ramp angle references remain in drivetrain Physical Principles
grep -n "ramp angle" backend/ac_engineer/knowledge/docs/drivetrain.md

# Verify springs-transfer-speed attribution fixed
grep -in "springs govern the transient rate" backend/ac_engineer/knowledge/docs/suspension_and_springs.md
```

## Document Edit Order (from audit report)

1. `tyre_dynamics.md` — brush model, load sensitivity, SAT, relaxation length
2. `vehicle_balance_fundamentals.md` — transfer attribution, decomposition, TLLTD
3. `telemetry_and_diagnosis.md` — sample rate, G-G diagram, reframe symptom table
4. `suspension_and_springs.md` — wheel rate clarification, transfer speed fix, roll center
5. `drivetrain.md` — lock percentages throughout, remove ramp angle terminology
6. `braking.md` — car-specific parameter availability notes
7. `dampers.md` — AC parameter names, velocity domains, damping ratios
8. `alignment.md` — adjustable vs fixed parameters, dynamic camber
9. `aero_balance.md` — AC independent wing model, CoP vs CoG, L/D ratio
10. `setup_methodology.md` — OVAT limits, lap count, sensitivity hierarchy

## Critical Constraints

- **DO NOT** change section titles (must remain exactly: "Physical Principles", "Adjustable Parameters and Effects", "Telemetry Diagnosis", "Cross-References")
- **DO NOT** change document filenames
- **DO NOT** add new documents
- **DO** preserve the existing prose style (bold subheadings, paragraph-based, not bullet-heavy)
- **DO** maintain the 3-layer approach: physics → metrics → setup levers
