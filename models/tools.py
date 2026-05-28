from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


ToolName = Literal[
    "create_project",
    "save_raw_input",
    "transcribe_audio",
    "clean_transcript",
    "ingest_material",
    "run_gap_analysis",
    "render_prompt",
    "render_readiness",
    "build_workspace",
    "run_validation_suite",
    "write_decision",
    "create_snapshot",
    "inspect_link",
]


class ToolAction(BaseModel):
    """A single tool action proposed by Gemma."""

    tool: ToolName
    reason: str  # Why the agent chose this action
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """The outcome of executing a tool action."""

    tool: str
    success: bool
    output: str = ""
    error: str = ""
    state_changed: bool = False


class AgentDecision(BaseModel):
    """Structured output schema for Gemma's next-action decision."""

    observation: str  # What the agent observes about current state
    reasoning: str  # Why it chose this action
    action: ToolAction
    done: bool = False  # True when the agent believes no more actions needed


class ActionRecord(BaseModel):
    """Persisted log of one agent loop iteration."""

    step: int
    decision: AgentDecision
    result: ToolResult
    timestamp: str = Field(default_factory=utc_now_iso)
