"""Engineer pipeline — background job factories for AI engineer and chat."""

from __future__ import annotations

import logging
import json
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from ac_engineer.config.io import get_effective_model, read_config
from ac_engineer.config.models import ACConfig
from ac_engineer.engineer.agents import (
    DOMAIN_TOOLS,
    analyze_with_engineer,
    build_model,
    extract_tool_calls,
)
from ac_engineer.engineer.models import AgentDeps, SessionSummary
from ac_engineer.engineer.summarizer import summarize_session
from ac_engineer.resolver import resolve_parameters
from ac_engineer.storage.messages import get_messages, save_message
from ac_engineer.storage.models import LlmEvent
from ac_engineer.storage.recommendations import get_recommendations
from ac_engineer.storage.sessions import get_session, update_session_state
from ac_engineer.storage.usage import save_llm_event

from api.analysis.cache import get_cache_dir, load_analyzed_session
from api.engineer.cache import save_engineer_response

logger = logging.getLogger(__name__)


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
            from api.paths import get_traces_dir

            response = await analyze_with_engineer(
                summary,
                config,
                Path(db_path),
                ac_install_path=config.ac_install_path,
                parameter_ranges=resolved.parameters,
                resolution_tier=resolved.tier,
                diagnostic_mode=config.diagnostic_mode,
                traces_dir=get_traces_dir(),
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

        # Try to build AgentDeps and register tools for richer responses
        deps = None
        tools = None
        try:
            session_rec = get_session(db_path, session_id)
            car_name = session_rec.car if session_rec else summary.car_name
            resolved = resolve_parameters(
                config.ac_install_path,
                car_name,
                Path(db_path),
                session_setup=summary.active_setup_parameters,
            )
            deps = AgentDeps(
                session_summary=summary,
                parameter_ranges=resolved.parameters,
                knowledge_fragments=[],
            )
            tools = DOMAIN_TOOLS["principal"]
        except Exception:
            logger.warning(
                "Failed to build AgentDeps for chat, proceeding without tools",
                exc_info=True,
            )

        if deps is not None and tools is not None:
            agent: Agent = Agent(
                model,
                deps_type=AgentDeps,
                system_prompt=system_prompt,
            )
            for tool_fn in tools:
                agent.tool(tool_fn)
        else:
            agent = Agent(
                model,
                system_prompt=system_prompt,
            )
            deps = None

        effective_model = get_effective_model(config)
        start_time = time.perf_counter()

        result = await agent.run(
            user_content,
            message_history=message_history,
            deps=deps,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        assistant_content = result.output

        await update(90, "Saving assistant response...")
        assistant_msg = save_message(db_path, session_id, "assistant", assistant_content)

        # Capture diagnostic trace (non-critical — never block message delivery)
        if config.diagnostic_mode:
            try:
                from ac_engineer.engineer.trace import (
                    format_trace_markdown,
                    serialize_agent_trace,
                    write_trace,
                )
                from api.paths import get_traces_dir

                trace_dict = serialize_agent_trace(
                    "principal", system_prompt, user_content, result,
                )
                trace_content = format_trace_markdown(
                    session_id, "message", assistant_msg.message_id,
                    [trace_dict],
                )
                write_trace(
                    get_traces_dir(), "msg", assistant_msg.message_id,
                    trace_content,
                )
                logger.info(
                    "Wrote diagnostic trace for message %s",
                    assistant_msg.message_id,
                )
            except Exception:
                logger.warning("Failed to capture chat trace", exc_info=True)

        # Capture usage (non-critical — never block message delivery)
        try:
            usage = result.usage()
            tool_calls = extract_tool_calls(result)
            llm_event = LlmEvent(
                session_id=session_id,
                event_type="chat",
                agent_name="principal",
                model=effective_model,
                input_tokens=usage.input_tokens or 0,
                output_tokens=usage.output_tokens or 0,
                cache_read_tokens=usage.cache_read_tokens or 0,
                cache_write_tokens=usage.cache_write_tokens or 0,
                request_count=usage.requests or 0,
                tool_call_count=usage.tool_calls or 0,
                duration_ms=duration_ms,
                context_type="message",
                context_id=assistant_msg.message_id,
                tool_calls=tool_calls,
            )
            save_llm_event(db_path, llm_event)
        except Exception:
            logger.warning("Failed to capture chat usage", exc_info=True)

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
