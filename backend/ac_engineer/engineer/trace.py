"""Agent diagnostic trace serialization and I/O.

Captures multi-turn Pydantic AI agent conversations as human-readable
Markdown files for debugging and inspection.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

logger = logging.getLogger(__name__)


def serialize_agent_trace(
    domain: str,
    system_prompt: str,
    user_prompt: str,
    result: Any,
) -> dict:
    """Extract all messages from a Pydantic AI result into a structured dict.

    Iterates ``result.all_messages()`` and handles each message part type.
    Returns an AgentTrace-like dict (see data-model.md).
    """
    messages: list[dict] = []
    structured_output: dict | None = None

    for message in result.all_messages():
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, SystemPromptPart):
                    # Already captured separately
                    continue
                if isinstance(part, UserPromptPart):
                    # Already captured separately
                    continue
                if isinstance(part, ToolReturnPart):
                    content = part.content
                    if not isinstance(content, str):
                        try:
                            content = json.dumps(content, default=str)
                        except (TypeError, ValueError):
                            content = str(content)
                    messages.append({
                        "role": "tool_response",
                        "content": content,
                        "tool_name": part.tool_name,
                        "tool_call_id": part.tool_call_id,
                    })
        elif isinstance(message, ModelResponse):
            for part in message.parts:
                if isinstance(part, TextPart):
                    messages.append({
                        "role": "assistant",
                        "content": part.content,
                        "tool_name": None,
                        "tool_call_id": None,
                    })
                elif isinstance(part, ToolCallPart):
                    args = part.args
                    if isinstance(args, str):
                        args_str = args
                    else:
                        try:
                            args_str = json.dumps(args, default=str, indent=2)
                        except (TypeError, ValueError):
                            args_str = str(args)
                    messages.append({
                        "role": "tool_call",
                        "content": args_str,
                        "tool_name": part.tool_name,
                        "tool_call_id": part.tool_call_id,
                    })

    # Try to extract structured output
    try:
        output = result.output
        if output is not None and hasattr(output, "model_dump"):
            structured_output = output.model_dump()
    except Exception:
        pass

    return {
        "domain": domain,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "messages": messages,
        "structured_output": structured_output,
    }


def format_trace_markdown(
    session_id: str,
    trace_type: str,
    context_id: str,
    agent_traces: list[dict],
    timestamp: datetime | None = None,
) -> str:
    """Format agent trace dicts into a single Markdown string."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    domains = ", ".join(t["domain"] for t in agent_traces)
    ts_str = timestamp.isoformat()

    lines = [
        f"# Diagnostic Trace: {trace_type}",
        "",
        f"**ID**: {context_id}",
        f"**Session**: {session_id}",
        f"**Timestamp**: {ts_str}",
        f"**Agents**: {domains}",
        "",
        "---",
    ]

    for trace in agent_traces:
        lines.append("")
        lines.append(f"## Agent: {trace['domain']}")
        lines.append("")
        lines.append("### System Prompt")
        lines.append("")
        lines.append(trace["system_prompt"])
        lines.append("")
        lines.append("### User Prompt")
        lines.append("")
        lines.append(trace["user_prompt"])
        lines.append("")
        lines.append("### Conversation")

        for msg in trace["messages"]:
            lines.append("")
            if msg["role"] == "assistant":
                lines.append("#### Assistant")
                lines.append("")
                lines.append(msg["content"])
            elif msg["role"] == "tool_call":
                lines.append(f"#### Tool Call: {msg['tool_name']}")
                lines.append("")
                lines.append("```json")
                lines.append(msg["content"])
                lines.append("```")
            elif msg["role"] == "tool_response":
                lines.append(f"#### Tool Response: {msg['tool_name']}")
                lines.append("")
                lines.append("```json")
                lines.append(msg["content"])
                lines.append("```")

        lines.append("")
        lines.append("### Structured Output")
        lines.append("")
        if trace["structured_output"] is not None:
            lines.append("```json")
            lines.append(json.dumps(trace["structured_output"], indent=2, default=str))
            lines.append("```")
        else:
            lines.append("null")

        lines.append("")
        lines.append("---")

    return "\n".join(lines)


def write_trace(
    traces_dir: Path,
    trace_type: str,
    context_id: str,
    content: str,
) -> Path:
    """Write trace Markdown to ``{traces_dir}/{type}_{id}.md``.

    Creates the directory if needed.  Returns the file path.
    """
    traces_dir.mkdir(parents=True, exist_ok=True)
    file_path = traces_dir / f"{trace_type}_{context_id}.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def read_trace(
    traces_dir: Path,
    trace_type: str,
    context_id: str,
) -> str | None:
    """Read trace file content, or return ``None`` if it doesn't exist."""
    file_path = traces_dir / f"{trace_type}_{context_id}.md"
    if not file_path.is_file():
        return None
    return file_path.read_text(encoding="utf-8")
