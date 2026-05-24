from __future__ import annotations

from dataclasses import dataclass

from amadeus.core.gap_analysis import GapAnalysisResult, GapAnalyzer
from amadeus.core.generator import ProjectGenerator
from amadeus.core.readiness import ReadinessGate
from amadeus.core.scaffolder import ProjectScaffolder
from amadeus.core.state_store import ProjectStateStore
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectPhase, ProjectState


@dataclass
class HandoffBuildResult:
    project_path: str
    state: ProjectState
    gap_analysis: GapAnalysisResult
    readiness_report: str
    built: bool
    blocked: bool
    state_path: str = ""
    message: str = ""


def prepare_handoff_workspace(
    requirements: RequirementsModel,
    raw_text: str,
    output_dir: str,
    approve_readiness: bool = False,
    approval_note: str = "",
    channel: str = "cli",
    input_kind: str = "text",
    transcript_language: str = "de",
) -> HandoffBuildResult:
    """Run the Amadeus state, gap, readiness, and build pipeline."""

    state_store = ProjectStateStore()
    project_path = state_store.expected_project_path(output_dir, requirements.project_name)
    state = state_store.create_for_text(
        requirements=requirements,
        raw_text=raw_text,
        target_path=project_path,
        channel=channel,
        input_kind=input_kind,
        transcript_language=transcript_language,
    )

    gap_analyzer = GapAnalyzer()
    gap_analysis = gap_analyzer.analyze(requirements, state, raw_text)
    state = gap_analyzer.apply_to_state(state, gap_analysis)

    readiness_gate = ReadinessGate()
    if approve_readiness and not readiness_gate.can_build(state):
        state = readiness_gate.approve(
            state,
            approval_note
            or "User explicitly approved building with documented readiness gaps.",
        )

    readiness_report = readiness_gate.render_markdown(state)
    if not readiness_gate.can_build(state):
        state_path = state_store.save(state, project_path)
        state_store.save_gap_analysis(gap_analysis, project_path)
        state_store.save_readiness_report(readiness_report, project_path)
        return HandoffBuildResult(
            project_path=project_path,
            state=state,
            gap_analysis=gap_analysis,
            readiness_report=readiness_report,
            built=False,
            blocked=True,
            state_path=str(state_path),
            message=(
                "Readiness gate blocked the build. Resolve blockers or rerun with "
                "--approve-readiness and a documented approval note."
            ),
        )

    state.transition_to(ProjectPhase.WORKSPACE_BUILD)
    readiness_report = readiness_gate.render_markdown(state)
    generated_files = ProjectGenerator().generate_all_files(
        requirements,
        state=state,
        readiness_report=readiness_report,
    )
    scaffolded_path = ProjectScaffolder(base_output_dir=output_dir).scaffold(
        requirements,
        generated_files,
    )
    if not scaffolded_path:
        return HandoffBuildResult(
            project_path=project_path,
            state=state,
            gap_analysis=gap_analysis,
            readiness_report=readiness_report,
            built=False,
            blocked=False,
            message="Workspace scaffolding failed.",
        )

    state.transition_to(ProjectPhase.HANDOFF_READY)
    readiness_report = readiness_gate.render_markdown(state)
    state_path = state_store.save(state, scaffolded_path)
    state_store.save_gap_analysis(gap_analysis, scaffolded_path)
    state_store.save_readiness_report(readiness_report, scaffolded_path)
    return HandoffBuildResult(
        project_path=scaffolded_path,
        state=state,
        gap_analysis=gap_analysis,
        readiness_report=readiness_report,
        built=True,
        blocked=False,
        state_path=str(state_path),
        message="Handoff workspace created.",
    )
