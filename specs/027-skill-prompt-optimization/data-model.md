# Data Model: Skill Prompt Optimization

**Feature**: 027-skill-prompt-optimization
**Date**: 2026-03-09

## No Data Model Changes

This feature modifies only markdown prompt files. No Pydantic models, database tables, API schemas, or frontend types are created or modified.

The existing models that agents populate remain unchanged:

- **SetupChange**: Fields `reasoning` and `expected_effect` are constrained by prompt instructions, not schema changes.
- **DriverFeedback**: Fields `observation` and `suggestion` are constrained by prompt instructions, not schema changes.
- **SpecialistResult**: The max-3 limit on `setup_changes` / `driver_feedback` is enforced by prompt instructions, not model validators.
- **EngineerResponse**: The `summary` field length is constrained by the orchestrator prompt, not schema changes.

All constraints are soft (prompt-based) rather than hard (code-based), as specified in FR-006: "This evaluation is expressed as a prompt instruction to the agent, not as code logic."
