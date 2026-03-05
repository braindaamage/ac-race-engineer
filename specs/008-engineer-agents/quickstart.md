# Quickstart: Engineer Agents

**Feature**: 008-engineer-agents

## Prerequisites

```bash
# Activate conda environment
conda activate ac-race-engineer

# Install new dependency
pip install pydantic-ai[anthropic]
# Or for other providers:
# pip install pydantic-ai[openai]
# pip install pydantic-ai[google]
```

## Run Tests

```bash
# All engineer tests (Phase 5.2 + 5.3)
conda run -n ac-race-engineer pytest backend/tests/engineer/ -v

# Only agent tests (Phase 5.3)
conda run -n ac-race-engineer pytest backend/tests/engineer/test_agents.py backend/tests/engineer/test_tools.py backend/tests/engineer/test_integration.py -v

# Full test suite
conda run -n ac-race-engineer pytest backend/tests/ -v
```

No real LLM calls are made in tests — all use Pydantic AI TestModel/FunctionModel.

## Usage Example

```python
import asyncio
from pathlib import Path
from ac_engineer.config import read_config
from ac_engineer.engineer import summarize_session, analyze_with_engineer
from ac_engineer.storage import init_db

async def main():
    # Load config
    config = read_config(Path("data/config.json"))

    # Initialize database
    db_path = Path("data/ac_engineer.db")
    init_db(db_path)

    # Assume you have an AnalyzedSession from the analyzer pipeline
    # summary = summarize_session(analyzed_session, config)

    # Run AI analysis
    response = await analyze_with_engineer(
        summary=summary,
        config=config,
        db_path=db_path,
    )

    # Inspect results
    print(f"Summary: {response.summary}")
    print(f"Confidence: {response.confidence}")
    print(f"Signals addressed: {response.signals_addressed}")

    for change in response.setup_changes:
        print(f"\n{change.section}: {change.value_before} → {change.value_after}")
        print(f"  Why: {change.reasoning}")
        print(f"  Effect: {change.expected_effect}")

    for feedback in response.driver_feedback:
        print(f"\n[{feedback.area}] {feedback.observation}")
        print(f"  Suggestion: {feedback.suggestion}")

asyncio.run(main())
```

## Apply Recommendations

```python
from ac_engineer.engineer import apply_recommendation

outcomes = await apply_recommendation(
    recommendation_id=response.recommendation_id,
    setup_path=Path("data/setups/my_car/my_setup.ini"),
    db_path=db_path,
    ac_install_path=config.ac_install_path,
    car_name="my_car",
)

for outcome in outcomes:
    print(f"{outcome.section}: {outcome.old_value} → {outcome.new_value}")
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/ac_engineer/engineer/agents.py` | Agent definitions and orchestrator |
| `backend/ac_engineer/engineer/tools.py` | Tool implementations for agents |
| `backend/ac_engineer/engineer/skills/*.md` | System prompts for each specialist |
| `backend/tests/engineer/test_agents.py` | Agent orchestration tests |
| `backend/tests/engineer/test_tools.py` | Tool function tests |
| `backend/tests/engineer/test_integration.py` | End-to-end pipeline tests |
