# Quickstart: Token Optimization

**Feature**: 026-token-optimization
**Date**: 2026-03-09

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- All existing backend tests passing

## Files to Modify

Only two source files:
- `backend/ac_engineer/engineer/tools.py`
- `backend/ac_engineer/engineer/agents.py`

Test files to update:
- `backend/tests/engineer/test_tools.py`
- `backend/tests/engineer/test_agents.py`

## Running Tests

```bash
conda activate ac-race-engineer
pytest backend/tests/engineer/ -v
```

Full backend suite:
```bash
pytest backend/tests/ -v
```

## Key Import Paths

```python
# Knowledge module (existing)
from ac_engineer.knowledge import get_knowledge_for_signals
from ac_engineer.knowledge.index import SIGNAL_MAP
from ac_engineer.knowledge.models import KnowledgeFragment

# Pydantic AI (existing)
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded

# Engineer models (existing)
from ac_engineer.engineer.models import AgentDeps, SpecialistResult
```

## Verification Checklist

1. `get_current_value` no longer exists in tools.py
2. `get_current_value` no longer imported in agents.py
3. `get_setup_range` accepts `sections: list[str]`
4. `get_lap_detail` accepts `lap_numbers: list[int]`
5. `get_corner_metrics` accepts `corner_numbers: list[int]`
6. `search_kb` limits to 2 results with updated docstring
7. `_build_user_prompt` includes knowledge fragments section
8. `agent.run()` uses `max_turns=5`
9. `UnexpectedModelBehavior` caught per agent with warning log
10. All existing tests pass (updated for new signatures)
