from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from amadeus.core.gap_analysis import GapAnalysisResult, GapAnalyzer
from amadeus.core.generator import ProjectGenerator
from amadeus.core.readiness import ReadinessGate
from amadeus.core.scaffolder import ProjectScaffolder
from amadeus.core.state_store import ProjectStateStore
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectPhase, ProjectState

logger = logging.getLogger(__name__)


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


def _ingest_materials(state: ProjectState, source_files: list[Path]) -> ProjectState:
    """Ingest all provided source files into _sources/ and _context/."""
    from amadeus.core.material_ingestion import ingest_material
    from amadeus.models.state import MaterialRecord

    project_root = Path(state.target_path)
    context_dir = project_root / "_context"
    sources_dir = project_root / "_sources"
    context_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    for source_path in source_files:
        # 1. Original in _sources/ kopieren
        dest = sources_dir / source_path.name
        if source_path.exists() and source_path.is_file():
            shutil.copy2(source_path, dest)

        # 2. Konvertieren nach _context/
        result = ingest_material(source_path, context_dir)

        # 3. MaterialRecord im State registrieren
        context_path = ""
        if result.context_path:
            try:
                context_path = str(
                    Path(result.context_path).resolve().relative_to(project_root.resolve())
                ).replace("\\", "/")
            except ValueError:
                context_path = str(result.context_path).replace("\\", "/")

        record = MaterialRecord(
            source_id=result.source_id,
            original_path=f"_sources/{source_path.name}",
            context_path=context_path,
            material_type=source_path.suffix.lstrip("."),
            purpose="User-provided material",
            status="converted" if result.status == "ingested" else "failed",
            extraction_notes=list(result.extraction_notes),
        )
        state.materials.append(record)

    return state


def prepare_handoff_workspace(
    requirements: RequirementsModel,
    raw_text: str,
    output_dir: str,
    approve_readiness: bool = False,
    approval_note: str = "",
    channel: str = "cli",
    input_kind: str = "text",
    transcript_language: str = "de",
    source_files: list[Path] | None = None,
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

    if source_files:
        state = _ingest_materials(state, source_files)

    gap_analyzer = GapAnalyzer()
    gap_analysis = gap_analyzer.analyze(requirements, state, raw_text)
    state = gap_analyzer.apply_to_state(state, gap_analysis)

    readiness_gate = ReadinessGate()
    if approve_readiness and not readiness_gate.can_build(state):
        state = readiness_gate.approve(
            state,
            approval_note or "User explicitly approved building with documented readiness gaps.",
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
        state=state,
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

    from amadeus.core.workspace_validator import validate_workspace

    validation_errors = validate_workspace(scaffolded_path)
    if validation_errors:
        # Just logging the warnings, build is not aborted
        for err in validation_errors:
            logger.warning("Workspace validation warning: %s", err)

    state.transition_to(ProjectPhase.HANDOFF_READY)
    readiness_report = readiness_gate.render_markdown(state)
    state_path = state_store.save(state, scaffolded_path)
    state_store.save_gap_analysis(gap_analysis, scaffolded_path)
    state_store.save_readiness_report(readiness_report, scaffolded_path)

    from amadeus.core.versioning import create_workspace_snapshot

    create_workspace_snapshot(scaffolded_path, "Initial workspace build")

    from amadeus.core.validation_suite import run_validation_suite, save_validation_report

    validation_report = run_validation_suite(
        Path(scaffolded_path),
        state=state,
        requirements=requirements,
        raw_text=raw_text,
    )
    logger.info("%s", validation_report.summary())
    for issue in validation_report.issues:
        if issue.severity == "error":
            logger.warning("Validation suite error: %s", issue.message)
    save_validation_report(scaffolded_path, validation_report)

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
