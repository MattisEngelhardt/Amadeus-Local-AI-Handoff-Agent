from __future__ import annotations

import json
import shutil

from amadeus.core.validation_suite import (
    VALIDATOR_NAMES,
    run_validation_suite,
    validate_gap_analysis,
    validate_handoff_anatomy,
    validate_material_coverage,
    validate_prompt,
    validate_source_map,
    validate_transcript,
    validate_workspace_tree,
)
from amadeus.core.workspace_validator import (
    AGENTS_REQUIRED_SECTIONS,
    CLAUDE_REQUIRED_SECTIONS,
)
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import (
    GapItem,
    MaterialRecord,
    ProjectPhase,
    ProjectState,
    ReadinessSnapshot,
)


def _requirements() -> RequirementsModel:
    return RequirementsModel(
        project_name="validation-workspace",
        display_name="Validation Workspace",
        short_description="Prepare a validated handoff workspace.",
        project_type="AI handoff workspace",
        tech_stack=["Python"],
        dependencies=[],
        specifications=["Build a weather API handoff workspace."],
        quality_criteria=["Keep validation issues actionable."],
        files_to_create=[],
    )


def _assumption_gap() -> GapItem:
    return GapItem(
        gap_id="gap-assumption",
        category="assumption",
        title="No deployment target specified",
        detail="The executing agent should keep deployment configurable.",
        status="recorded",
    )


def _blocker_gap(status: str = "open") -> GapItem:
    return GapItem(
        gap_id="gap-blocker",
        category="blocker",
        title="Missing source file",
        detail="The requested source file was not provided.",
        status=status,  # type: ignore[arg-type]
    )


def _material(status: str = "converted") -> MaterialRecord:
    return MaterialRecord(
        source_id="brief",
        original_path="_sources/brief.txt",
        context_path="_context/brief.md" if status == "converted" else "",
        material_type="txt",
        purpose="Client brief",
        status=status,  # type: ignore[arg-type]
        extraction_notes=["Plain text material ingested as UTF-8."],
    )


def _state(
    *,
    with_material: bool = True,
    gaps: list[GapItem] | None = None,
    phase: ProjectPhase = ProjectPhase.HANDOFF_READY,
    readiness_score: int = 91,
) -> ProjectState:
    return ProjectState(
        project_name="validation-workspace",
        display_name="Validation Workspace",
        main_goal="Prepare a validated handoff workspace.",
        phase=phase,
        target_path="",
        materials=[_material()] if with_material else [],
        gaps=gaps if gaps is not None else [_assumption_gap()],
        readiness=ReadinessSnapshot(score=readiness_score, can_build=True),
    )


def _complete_prompt() -> str:
    sections = [
        "Context",
        "Role",
        "Goal",
        "Requirements",
        "Non-Goals",
        "Working Materials",
        "Output Expectations",
        "Working Method",
        "Quality Criteria",
        "Open Questions",
    ]
    body = "\n\n".join(f"## {section}\n\nContent." for section in sections)
    return f"# Master Prompt\n\n{body}\n"


def _complete_claude_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in CLAUDE_REQUIRED_SECTIONS)
    return (
        "# Project Brain\n\n"
        "- [Source provenance](SOURCE_MAP.md#source-map)\n"
        "- [Context materials](CONTEXT_INDEX.md#materials)\n\n"
        f"{sections}\n"
    )


def _complete_agents_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in AGENTS_REQUIRED_SECTIONS)
    return f"# Agent Instructions\n\nRead NEXT_STEPS.md first.\n\n{sections}\n"


def _write_gap_file(project_path, gaps: list[GapItem]) -> None:
    blockers = [gap.model_dump() for gap in gaps if gap.category == "blocker"]
    assumptions = [gap.model_dump() for gap in gaps if gap.category == "assumption"]
    optional_items = [gap.model_dump() for gap in gaps if gap.category == "optional"]
    payload = {
        "blockers": blockers,
        "assumptions": assumptions,
        "optional_items": optional_items,
        "missing_materials": [],
        "targeted_questions": [],
        "readiness_score": 91,
    }
    (project_path / "_logs" / "gap_analysis.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _write_complete_workspace(project_path, *, with_material: bool = True) -> ProjectState:
    for directory in ["_context", "_sources", "_skills", "_versions", "_logs"]:
        (project_path / directory).mkdir(parents=True, exist_ok=True)

    (project_path / "CLAUDE.md").write_text(_complete_claude_md(), encoding="utf-8")
    (project_path / "AGENTS.md").write_text(_complete_agents_md(), encoding="utf-8")
    (project_path / "MASTER_PROMPT.md").write_text(_complete_prompt(), encoding="utf-8")

    for file_name in [
        "PROJECT_BRIEF.md",
        "REQUIREMENTS.md",
        "DECISIONS.md",
        "NEXT_STEPS.md",
    ]:
        (project_path / file_name).write_text(f"# {file_name}\n\nContent.\n", encoding="utf-8")

    state = _state(with_material=with_material)
    if with_material:
        (project_path / "_sources" / "brief.txt").write_text("Brief", encoding="utf-8")
        (project_path / "_context" / "brief.md").write_text("# Brief\n", encoding="utf-8")
        source_rows = "| brief | `_sources/brief.txt` | `_context/brief.md` | Brief | converted |"
        context_rows = "| 1 | `_context/brief.md` | txt | Client brief | OK |"
    else:
        source_rows = "| - | - | - | - | - |"
        context_rows = "| - | - | - | - | - |"
        state = _state(with_material=False)

    (project_path / "SOURCE_MAP.md").write_text(
        "# Source Map\n\n"
        "| Source ID | Original | Converted | Purpose | Status |\n"
        "|---|---|---|---|---|\n"
        f"{source_rows}\n",
        encoding="utf-8",
    )
    (project_path / "CONTEXT_INDEX.md").write_text(
        "# Context Index\n\n"
        "## Materials\n\n"
        "| # | Context File | Type | Purpose | Extraction Notes |\n"
        "|---|---|---|---|---|\n"
        f"{context_rows}\n",
        encoding="utf-8",
    )

    (project_path / "_logs" / "raw_input.md").write_text(
        "# Raw Input\n\nBuild a validated handoff workspace.\n",
        encoding="utf-8",
    )
    _write_gap_file(project_path, state.gaps)

    snapshot_dir = project_path / "_versions" / "2026-05-27_0900"
    snapshot_dir.mkdir()
    (snapshot_dir / "SNAPSHOT.md").write_text("# Snapshot\n", encoding="utf-8")

    return state


def _has_issue(issues, severity: str, text: str) -> bool:
    return any(issue.severity == severity and text in issue.message for issue in issues)


def test_transcript_validator_passes_with_populated_raw_input(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)

    issues = validate_transcript(tmp_path, state)

    assert issues == []


def test_transcript_validator_warns_on_empty_raw_input(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "_logs" / "raw_input.md").write_text("# Raw Input\n", encoding="utf-8")

    issues = validate_transcript(tmp_path, state)

    assert _has_issue(issues, "warning", "contains no captured input")


def test_transcript_validator_errors_on_missing_raw_input(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "_logs" / "raw_input.md").unlink()

    issues = validate_transcript(tmp_path, state)

    assert _has_issue(issues, "error", "raw_input.md is missing")


def test_prompt_validator_passes_complete_prompt(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)

    issues = validate_prompt(tmp_path)

    assert issues == []


def test_prompt_validator_detects_missing_sections(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "MASTER_PROMPT.md").write_text(
        "# Master Prompt\n\n## Context\n\nOnly one section.\n",
        encoding="utf-8",
    )

    issues = validate_prompt(tmp_path)

    assert _has_issue(issues, "warning", "missing required section: Role")


def test_prompt_validator_detects_template_remnants(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "MASTER_PROMPT.md").write_text(
        _complete_prompt() + "\n{{ unresolved_value }}\n",
        encoding="utf-8",
    )

    issues = validate_prompt(tmp_path)

    assert _has_issue(issues, "error", "unresolved template markers")


def test_gap_validator_passes_with_valid_gap_file(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)

    issues = validate_gap_analysis(tmp_path, state)

    assert issues == []


def test_gap_validator_warns_on_missing_gap_file(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "_logs" / "gap_analysis.json").unlink()

    issues = validate_gap_analysis(tmp_path, state)

    assert _has_issue(issues, "warning", "gap_analysis.json is missing")


def test_gap_validator_errors_on_invalid_json(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "_logs" / "gap_analysis.json").write_text("{broken", encoding="utf-8")

    issues = validate_gap_analysis(tmp_path, state)

    assert _has_issue(issues, "error", "invalid JSON")


def test_gap_validator_errors_on_open_blocker_in_handoff_ready(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=False)
    state.gaps = [_blocker_gap()]
    _write_gap_file(tmp_path, state.gaps)

    issues = validate_gap_analysis(tmp_path, state)

    assert _has_issue(issues, "error", "Open blocker gap exists")


def test_material_validator_passes_with_converted_materials(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)

    issues = validate_material_coverage(tmp_path, state)

    assert issues == []


def test_material_validator_errors_on_missing_context_file(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "_context" / "brief.md").unlink()

    issues = validate_material_coverage(tmp_path, state)

    assert _has_issue(issues, "error", "context file is missing")


def test_material_validator_warns_on_failed_material(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)
    state = _state(with_material=False, gaps=[])
    state.materials = [
        MaterialRecord(
            source_id="failed",
            original_path="_sources/missing.pdf",
            material_type="pdf",
            status="failed",
            extraction_notes=["PDF adapter failed."],
        )
    ]

    issues = validate_material_coverage(tmp_path, state)

    assert _has_issue(issues, "warning", "Material failed conversion")
    assert _has_issue(issues, "warning", "PDF adapter failed")


def test_source_map_validator_passes_complete_map(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)

    issues = validate_source_map(tmp_path, state)

    assert issues == []


def test_source_map_validator_errors_on_broken_reference(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "SOURCE_MAP.md").write_text(
        "# Source Map\n\n`_sources/brief.txt` `_context/missing.md`\n",
        encoding="utf-8",
    )

    issues = validate_source_map(tmp_path, state)

    assert _has_issue(issues, "error", "references missing file: _context/missing.md")


def test_source_map_validator_warns_on_missing_material_in_map(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "SOURCE_MAP.md").write_text(
        "# Source Map\n\n`_context/brief.md`\n",
        encoding="utf-8",
    )

    issues = validate_source_map(tmp_path, state)

    assert _has_issue(issues, "warning", "original path is missing")


def test_workspace_tree_passes_valid_workspace(tmp_path):
    _write_complete_workspace(tmp_path, with_material=True)

    issues = validate_workspace_tree(tmp_path)

    assert issues == []


def test_workspace_tree_errors_on_missing_canonical_file(tmp_path):
    _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "DECISIONS.md").unlink()

    issues = validate_workspace_tree(tmp_path)

    assert _has_issue(issues, "error", "Missing canonical file: DECISIONS.md")


def test_workspace_tree_errors_on_missing_canonical_directory(tmp_path):
    _write_complete_workspace(tmp_path, with_material=True)
    shutil.rmtree(tmp_path / "_skills")

    issues = validate_workspace_tree(tmp_path)

    assert _has_issue(issues, "error", "Missing canonical directory: _skills")


def test_workspace_tree_warns_on_empty_file(tmp_path):
    _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "NEXT_STEPS.md").write_text(" \n", encoding="utf-8")

    issues = validate_workspace_tree(tmp_path)

    assert _has_issue(issues, "warning", "Canonical file is empty: NEXT_STEPS.md")


def test_handoff_anatomy_passes_complete_files(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)

    issues = validate_handoff_anatomy(tmp_path)

    assert issues == []


def test_handoff_anatomy_errors_on_missing_claude_section(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "CLAUDE.md").write_text(
        "# Project Brain\n\n## Role Alignment\n\nSee SOURCE_MAP.md and CONTEXT_INDEX.md.\n",
        encoding="utf-8",
    )

    issues = validate_handoff_anatomy(tmp_path)

    assert _has_issue(issues, "error", "CLAUDE.md missing required section")


def test_handoff_anatomy_errors_on_missing_agents_section(tmp_path):
    _write_complete_workspace(tmp_path, with_material=False)
    (tmp_path / "AGENTS.md").write_text(
        "# Agent Instructions\n\n## Project Direction\n\nRead NEXT_STEPS.md.\n",
        encoding="utf-8",
    )

    issues = validate_handoff_anatomy(tmp_path)

    assert _has_issue(issues, "error", "AGENTS.md missing required section")


def test_validation_suite_runs_all_validators(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)

    report = run_validation_suite(tmp_path, state=state, requirements=_requirements())

    assert report.validators_run == VALIDATOR_NAMES
    assert report.passed is True
    assert report.issues == []


def test_validation_suite_report_counts_are_correct(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "MASTER_PROMPT.md").write_text(
        _complete_prompt() + "\n{% unresolved %}\n",
        encoding="utf-8",
    )
    (tmp_path / "_logs" / "raw_input.md").unlink()

    report = run_validation_suite(tmp_path, state=state, requirements=None)

    assert report.error_count == 2
    assert report.warning_count == 0
    assert report.info_count == 1


def test_validation_suite_passed_is_false_when_errors_exist(tmp_path):
    state = _write_complete_workspace(tmp_path, with_material=True)
    (tmp_path / "SOURCE_MAP.md").unlink()

    report = run_validation_suite(tmp_path, state=state, requirements=_requirements())

    assert report.passed is False
    assert report.error_count > 0
