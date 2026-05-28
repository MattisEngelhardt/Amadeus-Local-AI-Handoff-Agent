from dataclasses import dataclass

from amadeus.models.tools import ToolName


@dataclass
class ToolContract:
    name: ToolName
    description: str
    required_params: list[str]
    optional_params: list[str]
    mode: str  # Which agent mode uses this tool


TOOL_REGISTRY: dict[ToolName, ToolContract] = {
    "create_project": ToolContract(
        name="create_project",
        description="Initialize a new Amadeus project with state and registry entry.",
        required_params=["raw_text"],
        optional_params=["project_name", "output_dir"],
        mode="intake",
    ),
    "save_raw_input": ToolContract(
        name="save_raw_input",
        description="Persist a raw text or voice input to the project state.",
        required_params=["raw_text", "channel", "kind"],
        optional_params=[],
        mode="intake",
    ),
    "ingest_material": ToolContract(
        name="ingest_material",
        description="Convert a source file into _sources/ and _context/.",
        required_params=["source_path"],
        optional_params=["source_id"],
        mode="intake",
    ),
    "run_gap_analysis": ToolContract(
        name="run_gap_analysis",
        description="Analyze gaps, blockers, and assumptions in the current state.",
        required_params=[],
        optional_params=[],
        mode="gap_analyst",
    ),
    "render_prompt": ToolContract(
        name="render_prompt",
        description="Generate or update MASTER_PROMPT.md from current state.",
        required_params=[],
        optional_params=[],
        mode="prompt_compiler",
    ),
    "render_readiness": ToolContract(
        name="render_readiness",
        description="Render the readiness gate report.",
        required_params=[],
        optional_params=[],
        mode="workspace_architect",
    ),
    "build_workspace": ToolContract(
        name="build_workspace",
        description="Generate and scaffold the full handoff workspace.",
        required_params=[],
        optional_params=["approve_readiness", "approval_note"],
        mode="build_orchestrator",
    ),
    "run_validation_suite": ToolContract(
        name="run_validation_suite",
        description="Run all 7 validators on the built workspace.",
        required_params=[],
        optional_params=[],
        mode="build_orchestrator",
    ),
    "write_decision": ToolContract(
        name="write_decision",
        description="Record a project decision in state.",
        required_params=["summary", "rationale"],
        optional_params=["approved_by_user"],
        mode="gap_analyst",
    ),
    "create_snapshot": ToolContract(
        name="create_snapshot",
        description="Create a version snapshot of the current workspace.",
        required_params=["reason"],
        optional_params=[],
        mode="build_orchestrator",
    ),
    "transcribe_audio": ToolContract(
        name="transcribe_audio",
        description="Transcribe audio file.",
        required_params=["audio_path"],
        optional_params=["language"],
        mode="transcription_review",
    ),
    "clean_transcript": ToolContract(
        name="clean_transcript",
        description="Clean a raw transcript.",
        required_params=["transcript_id"],
        optional_params=[],
        mode="transcription_review",
    ),
    "inspect_link": ToolContract(
        name="inspect_link",
        description="Inspect a URL link.",
        required_params=["url"],
        optional_params=[],
        mode="intake",
    ),
}
