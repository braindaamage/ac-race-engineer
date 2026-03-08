"""Engineer pipeline — background job factories for AI engineer and chat."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from ac_engineer.config.models import ACConfig
from ac_engineer.engineer.agents import analyze_with_engineer
from ac_engineer.engineer.agents import build_model
from ac_engineer.engineer.models import SessionSummary
from ac_engineer.engineer.summarizer import summarize_session
from ac_engineer.resolver import resolve_parameters
from ac_engineer.storage.messages import get_messages, save_message
from ac_engineer.storage.recommendations import get_recommendations
from ac_engineer.storage.sessions import update_session_state

from api.analysis.cache import get_cache_dir, load_analyzed_session
from api.engineer.cache import save_engineer_response


def make_engineer_job(
    session_id: str,
    sessions_dir: str | Path,
    db_path: str | Path,
    config: ACConfig,
    active_jobs: dict[str, str],
) -> Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[Any]]:
    """Build an async callable that runs the full engineer pipeline."""

    async def pipeline(
        update: Callable[[int, str], Awaitable[None]],
    ) -> dict[str, str]:
        try:
            await update(5, "Loading analyzed session...")
            cache_dir = get_cache_dir(sessions_dir, session_id)
            analyzed = load_analyzed_session(cache_dir)

            await update(15, "Loading setup contents...")
            setup_ini_contents = _load_setup_contents(cache_dir)

            await update(20, "Summarizing session for AI engineer...")
            summary = summarize_session(analyzed, config, setup_ini_contents=setup_ini_contents)

            await update(25, "Resolving parameter ranges...")
            resolved = resolve_parameters(
                config.ac_install_path,
                summary.car_name,
                Path(db_path),
                session_setup=summary.active_setup_parameters,
            )

            await update(30, "Running AI engineer analysis...")
            response = await analyze_with_engineer(
                summary,
                config,
                Path(db_path),
                ac_install_path=config.ac_install_path,
                parameter_ranges=resolved.parameters,
                resolution_tier=resolved.tier,
            )

            # Detect total failure: no changes, no feedback, low confidence
            analysis_failed = (
                not response.setup_changes
                and not response.driver_feedback
                and response.confidence == "low"
            )

            await update(85, "Caching engineer response...")
            recs = get_recommendations(db_path, session_id)
            if recs:
                rec_id = recs[-1].recommendation_id
                save_engineer_response(cache_dir, rec_id, response)

            if analysis_failed:
                # Keep session at "analyzed" so the user can retry
                return {"session_id": session_id, "state": "analyzed", "error": response.explanation}

            await update(95, "Updating session state...")
            update_session_state(db_path, session_id, "engineered")

            return {"session_id": session_id, "state": "engineered"}
        finally:
            active_jobs.pop(session_id, None)

    return pipeline


def make_chat_job(
    session_id: str,
    message_id: str,
    user_content: str,
    sessions_dir: str | Path,
    db_path: str | Path,
    config: ACConfig,
) -> Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[Any]]:
    """Build an async callable that generates an AI chat response."""

    async def pipeline(
        update: Callable[[int, str], Awaitable[None]],
    ) -> dict[str, str]:
        await update(5, "Loading session context...")
        cache_dir = get_cache_dir(sessions_dir, session_id)
        analyzed = load_analyzed_session(cache_dir)

        await update(10, "Loading setup contents...")
        setup_ini_contents = _load_setup_contents(cache_dir)

        await update(15, "Summarizing session for context...")
        summary = summarize_session(analyzed, config, setup_ini_contents=setup_ini_contents)

        await update(20, "Loading conversation history...")
        messages = get_messages(db_path, session_id)

        await update(30, "Generating AI response...")

        # Build system prompt with session context
        system_prompt = _build_chat_system_prompt(summary)

        # Build message history for the agent (exclude the current user message)
        message_history: list[ModelRequest | ModelResponse] = []
        for msg in messages:
            if msg.message_id == message_id:
                continue
            if msg.role == "user":
                message_history.append(
                    ModelRequest(parts=[UserPromptPart(content=msg.content)])
                )
            else:
                message_history.append(
                    ModelResponse(parts=[TextPart(content=msg.content)])
                )

        model = build_model(config)
        agent: Agent[None, str] = Agent(
            model,
            system_prompt=system_prompt,
        )

        result = await agent.run(
            user_content,
            message_history=message_history,
        )
        assistant_content = result.output

        await update(90, "Saving assistant response...")
        save_message(db_path, session_id, "assistant", assistant_content)

        return {"session_id": session_id, "message_id": message_id}

    return pipeline


def _build_chat_system_prompt(summary: SessionSummary) -> str:
    """Build the system prompt for the chat agent with session context."""
    skill_path = (
        Path(__file__).resolve().parent.parent.parent
        / "ac_engineer"
        / "engineer"
        / "skills"
        / "principal.md"
    )
    skill_prompt = ""
    if skill_path.exists():
        skill_prompt = skill_path.read_text(encoding="utf-8")

    summary_text = summary.model_dump_json(indent=2)

    return (
        f"{skill_prompt}\n\n"
        f"## Session Context\n\n"
        f"You are discussing the following session with the driver:\n\n"
        f"```json\n{summary_text}\n```\n\n"
        f"Answer the driver's questions about this session. "
        f"Be specific and reference data from the session context."
    )


def _load_setup_contents(cache_dir: Path) -> str | None:
    """Load the last setup .ini contents from the session's .meta.json."""
    meta_path = cache_dir.parent / f"{cache_dir.name}.meta.json"
    meta_files = [meta_path] if meta_path.is_file() else []
    if not meta_files:
        return None
    try:
        meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
        setup_history = meta.get("setup_history", [])
        for entry in reversed(setup_history):
            contents = entry.get("contents")
            if contents:
                return contents
    except (json.JSONDecodeError, OSError):
        pass
    return None
