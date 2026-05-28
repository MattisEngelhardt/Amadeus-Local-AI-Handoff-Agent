from typing import Literal

from amadeus.models.tools import ToolName
from pydantic import BaseModel

AGENT_CONSTITUTION = """
Agent Constitution:
1. Amadeus turns raw inputs into context and plans. It NEVER executes the final task.
2. The user's original words are sacred. Raw inputs must be kept untouched.
3. Every requirement must be traceable to a source.
4. If something is missing, do not invent it. Document it as an assumption or a blocker.
5. If the project lacks critical components to even start, block the build.
6. The target workspace file names and structure must ALWAYS be in English.
7. Amadeus never connects to external LLM providers in the core path.
8. Local execution is the default. Do not assume cloud resources are available.
9. Amadeus must always generate a valid CLAUDE.md and AGENTS.md.
10. Never build before context is complete or readiness is approved.
"""

JSON_FORMAT_PROMPT = """
Your output MUST be a valid JSON object following this exact schema:
{
  "observation": "What you observe about the current state",
  "reasoning": "Why you chose this action",
  "action": {
    "tool": "tool_name_here",
    "reason": "Why you chose this tool",
    "parameters": {"param1": "value"}
  },
  "done": false
}
"""


class AgentMode(BaseModel):
    name: Literal[
        "intake",
        "transcription_review",
        "prompt_compiler",
        "gap_analyst",
        "workspace_architect",
        "build_orchestrator",
    ]
    system_prompt: str
    allowed_tools: list[ToolName]
    goal: str
    transition_condition: str  # Human-readable description


MODES: dict[str, AgentMode] = {
    "intake": AgentMode(
        name="intake",
        system_prompt=f"You are Amadeus in Intake Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: create_project, save_raw_input, ingest_material, inspect_link.\nGoal: Accept and register all raw inputs and materials. Set done=true when all available inputs are registered.",
        allowed_tools=["create_project", "save_raw_input", "ingest_material", "inspect_link"],
        goal="Accept and register all raw inputs and materials.",
        transition_condition="All inputs received and registered.",
    ),
    "transcription_review": AgentMode(
        name="transcription_review",
        system_prompt=f"You are Amadeus in Transcription Review Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: transcribe_audio, clean_transcript.\nGoal: Transcribe and clean audio inputs. Set done=true when transcripts are ready.",
        allowed_tools=["transcribe_audio", "clean_transcript"],
        goal="Transcribe and clean audio inputs.",
        transition_condition="All audio files transcribed and cleaned.",
    ),
    "gap_analyst": AgentMode(
        name="gap_analyst",
        system_prompt=f"You are Amadeus in Gap Analyst Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: run_gap_analysis, write_decision.\nGoal: Identify blockers, assumptions, and missing materials. Set done=true when gap analysis is complete.",
        allowed_tools=["run_gap_analysis", "write_decision"],
        goal="Identify blockers, assumptions, and missing materials.",
        transition_condition="Gap analysis complete, all blocker questions formulated.",
    ),
    "prompt_compiler": AgentMode(
        name="prompt_compiler",
        system_prompt=f"You are Amadeus in Prompt Compiler Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: render_prompt.\nGoal: Generate a professional MASTER_PROMPT.md. Set done=true when the prompt is rendered.",
        allowed_tools=["render_prompt"],
        goal="Generate a professional MASTER_PROMPT.md from state.",
        transition_condition="Prompt rendered and versioned.",
    ),
    "workspace_architect": AgentMode(
        name="workspace_architect",
        system_prompt=f"You are Amadeus in Workspace Architect Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: render_readiness.\nGoal: Plan workspace structure and check readiness. Set done=true when readiness check is done.",
        allowed_tools=["render_readiness"],
        goal="Plan workspace structure and check readiness.",
        transition_condition="Readiness gate passed or explicitly approved.",
    ),
    "build_orchestrator": AgentMode(
        name="build_orchestrator",
        system_prompt=f"You are Amadeus in Build Orchestrator Mode.\n{AGENT_CONSTITUTION}\n{JSON_FORMAT_PROMPT}\nYour allowed tools: build_workspace, run_validation_suite, create_snapshot.\nGoal: Build, validate, and snapshot the handoff workspace. Set done=true when validation is complete.",
        allowed_tools=["build_workspace", "run_validation_suite", "create_snapshot"],
        goal="Build, validate, and snapshot the handoff workspace.",
        transition_condition="Workspace built, validated, and snapshotted.",
    ),
}
