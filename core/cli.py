import argparse
import os
from pathlib import Path

from amadeus.core.analyzer import TranscriptAnalyzer
from amadeus.core.gap_analysis import GapAnalyzer
from amadeus.core.project_registry import ProjectRegistry
from amadeus.core.state_store import ProjectStateStore
from amadeus.core.validation_suite import run_validation_suite
from amadeus.core.validator import RequirementsValidator
from amadeus.core.workflow import _ingest_materials, prepare_handoff_workspace
from amadeus.models.state import ProjectRegistryEntry


def _get_active_project_state(registry: ProjectRegistry):
    entry = registry.get_active()
    if not entry:
        print("FAIL: No active project. Run 'amadeus new' or 'amadeus use'.")
        return None, None
    state_file = Path(entry.project_path) / "_logs" / "amadeus_state.json"
    if not state_file.exists():
        print(f"FAIL: State file not found at {state_file}")
        return entry, None
    store = ProjectStateStore()
    state = store.load(Path(entry.project_path))
    return entry, state


def run_new_command(args: argparse.Namespace) -> int:
    analyzer = TranscriptAnalyzer(model=args.model, ollama_base_url=args.ollama_url)
    requirements = analyzer.analyze(args.text)
    if requirements is None:
        print("FAIL: Amadeus could not analyze the input. Check Ollama and the model first.")
        return 2

    validator = RequirementsValidator()
    requirements = validator.validate(args.text, requirements)

    output_dir = args.output_dir or str(Path.home() / ".amadeus" / "projects")
    store = ProjectStateStore()
    project_path = store.expected_project_path(output_dir, requirements.project_name)

    state = store.create_for_text(
        requirements=requirements,
        raw_text=args.text,
        target_path=project_path,
        channel="cli",
        input_kind="text",
    )

    gap_analyzer = GapAnalyzer()
    gap_analysis = gap_analyzer.analyze(requirements, state, args.text)
    state = gap_analyzer.apply_to_state(state, gap_analysis)

    store.save(state, Path(project_path))

    registry = ProjectRegistry()
    entry = ProjectRegistryEntry(
        project_name=state.project_name,
        display_name=state.display_name,
        project_path=project_path,
        phase=state.phase,
        readiness_score=state.readiness.score,
        is_active=True,
    )
    registry.register(entry)
    registry.set_active(state.project_name)

    print(f"Project '{state.project_name}' created at {project_path}")
    print(f"Readiness score: {state.readiness.score}/100")
    print("Project is now active. Add materials or run 'amadeus build'.")
    return 0


def run_add_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    files = [Path(f) for f in args.files]
    state = _ingest_materials(state, files)

    from amadeus.models.requirements import RequirementsModel

    req_model = (
        RequirementsModel.model_validate(state.requirements)
        if state.requirements
        else RequirementsModel(
            project_name=state.project_name,
            display_name=state.display_name,
            short_description=state.main_goal,
            project_type="unknown",
            tech_stack=[],
            dependencies=[],
            specifications=[],
            quality_criteria=[],
            files_to_create=[],
        )
    )
    reqs = RequirementsValidator().validate("", req_model)  # dummy raw text for dummy validate
    gap_analyzer = GapAnalyzer()
    gap_analysis = gap_analyzer.analyze(reqs, state, "")
    state = gap_analyzer.apply_to_state(state, gap_analysis)

    store = ProjectStateStore()
    store.save(state, Path(entry.project_path))
    registry.update_state(state.project_name, state)

    print(f"Added {len(files)} materials to project '{state.project_name}'.")
    print(f"Updated readiness score: {state.readiness.score}/100")
    return 0


def run_status_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    print(f"Project: {state.project_name} ({state.display_name})")
    print(f"Phase: {state.phase.value}")
    print(f"Readiness Score: {state.readiness.score}/100")
    print(f"Materials: {len(state.materials)}")
    print(f"Blockers: {len(state.open_blockers())}")
    print(f"Assumptions: {len(state.recorded_assumptions())}")
    return 0


def run_gaps_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    print(f"Gaps for '{state.project_name}':")

    blockers = state.open_blockers()
    if blockers:
        print("\n=== BLOCKERS ===")
        for b in blockers:
            print(f"- {b.title}: {b.detail}")
            if b.question:
                print(f"  Q: {b.question}")

    assumptions = state.recorded_assumptions()
    if assumptions:
        print("\n=== ASSUMPTIONS ===")
        for a in assumptions:
            print(f"- {a.title}: {a.detail}")

    optional = [g for g in state.gaps if g.category == "optional"]
    if optional:
        print("\n=== OPTIONAL ===")
        for o in optional:
            print(f"- {o.title}: {o.detail}")

    if not state.gaps:
        print("No gaps found.")
    return 0


def run_materials_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    print(f"Materials for '{state.project_name}':")
    for m in state.materials:
        print(f"- {m.source_id}: {m.original_path} -> {m.context_path} [{m.status}]")
        if m.extraction_notes:
            print(f"  Notes: {', '.join(m.extraction_notes)}")
    if not state.materials:
        print("No materials added.")
    return 0


def run_build_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    # Needs a raw_text. We grab it from raw_inputs if available, or just empty.
    raw_text = state.raw_inputs[0].raw_text if state.raw_inputs else ""

    from amadeus.models.requirements import RequirementsModel

    req_obj = (
        RequirementsModel.model_validate(state.requirements)
        if state.requirements
        else RequirementsModel(
            project_name=state.project_name,
            display_name=state.display_name,
            short_description=state.main_goal,
            project_type="unknown",
            tech_stack=[],
            dependencies=[],
            specifications=[],
            quality_criteria=[],
            files_to_create=[],
        )
    )
    req_model = RequirementsValidator().validate(raw_text, req_obj)

    # We call prepare_handoff_workspace again but it will override the state file.
    # To keep things clean and use the existing gap analysis, we should technically just
    # run readiness gate and build. But since we need to reuse prepare_handoff_workspace:
    result = prepare_handoff_workspace(
        requirements=req_model,
        raw_text=raw_text,
        output_dir=str(Path(entry.project_path).parent),
        approve_readiness=args.approve_readiness,
        approval_note=args.approval_note,
        channel="cli",
        input_kind="text",
        source_files=[],  # Already ingested
    )

    if result.blocked:
        print("BLOCKED: Readiness gate found open blockers.")
        for blocker in result.state.open_blockers():
            print(f"- {blocker.title}: {blocker.question}")
        return 4

    if not result.built:
        print(f"FAIL: {result.message}")
        return 3

    registry.update_state(result.state.project_name, result.state)
    print(f"OK: Workspace built at {result.project_path}")
    return 0


def run_validate_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry, state = _get_active_project_state(registry)
    if not state:
        return 1

    raw_text = state.raw_inputs[0].raw_text if state.raw_inputs else ""
    from amadeus.models.requirements import RequirementsModel

    req_obj = (
        RequirementsModel.model_validate(state.requirements)
        if state.requirements
        else RequirementsModel(
            project_name=state.project_name,
            display_name=state.display_name,
            short_description=state.main_goal,
            project_type="unknown",
            tech_stack=[],
            dependencies=[],
            specifications=[],
            quality_criteria=[],
            files_to_create=[],
        )
    )
    req_model = RequirementsValidator().validate(raw_text, req_obj)

    report = run_validation_suite(
        Path(entry.project_path), state=state, requirements=req_model, raw_text=raw_text
    )
    print(report.summary())
    return 0 if report.passed else 1


def run_projects_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entries = registry.list_projects()
    if not entries:
        print("No projects registered.")
        return 0
    print("Registered Projects:")
    for e in entries:
        active = "*" if e.is_active else " "
        print(
            f"{active} {e.project_name} ({e.phase.value}) - Readiness: {e.readiness_score}/100 - {e.project_path}"
        )
    return 0


def run_use_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entries = registry.list_projects()
    if any(e.project_name == args.project_name for e in entries):
        registry.set_active(args.project_name)
        print(f"Active project set to '{args.project_name}'.")
        return 0
    print(f"FAIL: Project '{args.project_name}' not found.")
    return 1


def run_open_command(args: argparse.Namespace) -> int:
    registry = ProjectRegistry()
    entry = registry.get_active()
    if not entry:
        print("FAIL: No active project.")
        return 1
    print(entry.project_path)
    if os.name == "nt":
        os.startfile(entry.project_path)
    return 0
