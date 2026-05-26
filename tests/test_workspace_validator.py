from __future__ import annotations

from amadeus.core.validation_suite import run_validation_suite
from amadeus.core.workspace_validator import (
    AGENTS_REQUIRED_SECTIONS,
    CLAUDE_REQUIRED_SECTIONS,
    validate_agents_md_anatomy,
    validate_claude_md_anatomy,
    validate_workspace,
)
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectPhase, ProjectState, ReadinessSnapshot


def _complete_claude_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in CLAUDE_REQUIRED_SECTIONS)
    return f"# Project Brain\n\n{sections}\n"


def _complete_agents_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in AGENTS_REQUIRED_SECTIONS)
    return f"# Agent Instructions\n\n{sections}\n"


def _complete_master_prompt() -> str:
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
    return "# Master Prompt\n\n" + "\n\n".join(
        f"## {section}\n\nContent." for section in sections
    )


def _requirements() -> RequirementsModel:
    return RequirementsModel(
        project_name="validator-regression",
        display_name="Validator Regression",
        short_description="Validate a handoff workspace.",
        project_type="AI handoff workspace",
        tech_stack=["Python"],
        dependencies=[],
        specifications=["Verify the workspace validators."],
        quality_criteria=["Keep validator output deterministic."],
        files_to_create=[],
    )


def test_validate_workspace_detects_missing_files_and_directories(tmp_path):
    errors = validate_workspace(tmp_path)

    assert any("Missing canonical file: CLAUDE.md" in e for e in errors)
    assert any("Missing canonical directory: _sources" in e for e in errors)

def test_validate_workspace_detects_empty_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("   \n", encoding="utf-8")
    errors = validate_workspace(tmp_path)
    assert "CLAUDE.md is empty" in errors

def test_validate_workspace_checks_source_map_references(tmp_path):
    source_map = tmp_path / "SOURCE_MAP.md"
    source_map.write_text("`_sources/missing.txt` and `_context/missing.md`", encoding="utf-8")

    errors = validate_workspace(tmp_path)
    assert "SOURCE_MAP.md references missing source file: _sources/missing.txt" in errors
    assert "SOURCE_MAP.md references missing context file: _context/missing.md" in errors

def test_validate_claude_md_anatomy_detects_missing_sections(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "# Project Brain\n\n## Role Alignment\n\nContent.\n",
        encoding="utf-8",
    )

    missing = validate_claude_md_anatomy(tmp_path)

    assert "Role Alignment" not in missing
    assert "Semantic File Map" in missing
    assert "Verification Checklist" in missing


def test_validate_claude_md_anatomy_passes_complete_file(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(_complete_claude_md(), encoding="utf-8")

    assert validate_claude_md_anatomy(tmp_path) == []


def test_validate_agents_md_anatomy_detects_missing_sections(tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        "# Agent Instructions\n\n## Project Direction\n\nContent.\n",
        encoding="utf-8",
    )

    missing = validate_agents_md_anatomy(tmp_path)

    assert "Project Direction" not in missing
    assert "Context-Reading Rules" in missing
    assert "Definition of Done" in missing


def test_validate_agents_md_anatomy_passes_complete_file(tmp_path):
    (tmp_path / "AGENTS.md").write_text(_complete_agents_md(), encoding="utf-8")

    assert validate_agents_md_anatomy(tmp_path) == []


def test_validate_workspace_passes_valid_workspace(tmp_path):
    canonical_files = [
        "CLAUDE.md",
        "AGENTS.md",
        "MASTER_PROMPT.md",
        "PROJECT_BRIEF.md",
        "REQUIREMENTS.md",
        "DECISIONS.md",
        "NEXT_STEPS.md",
        "CONTEXT_INDEX.md",
        "SOURCE_MAP.md",
    ]
    for f in canonical_files:
        (tmp_path / f).write_text("Content", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(_complete_claude_md(), encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(_complete_agents_md(), encoding="utf-8")

    for d in ["_context", "_sources", "_skills", "_versions", "_logs"]:
        (tmp_path / d).mkdir()

    (tmp_path / "SOURCE_MAP.md").write_text(
        "`_sources/test.txt` `_context/test.md`",
        encoding="utf-8",
    )
    (tmp_path / "_sources" / "test.txt").write_text("test", encoding="utf-8")
    (tmp_path / "_context" / "test.md").write_text("test", encoding="utf-8")

    errors = validate_workspace(tmp_path)
    assert not errors


def test_validate_workspace_still_passes_with_validation_suite(tmp_path):
    canonical_files = [
        "PROJECT_BRIEF.md",
        "REQUIREMENTS.md",
        "DECISIONS.md",
        "NEXT_STEPS.md",
    ]
    for file_name in canonical_files:
        (tmp_path / file_name).write_text("Content", encoding="utf-8")

    claude_md = (
        _complete_claude_md()
        + "\nSee SOURCE_MAP.md and CONTEXT_INDEX.md for source coverage.\n"
    )
    agents_md = _complete_agents_md() + "\nFollow NEXT_STEPS.md before execution.\n"
    (tmp_path / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(agents_md, encoding="utf-8")
    (tmp_path / "MASTER_PROMPT.md").write_text(_complete_master_prompt(), encoding="utf-8")
    (tmp_path / "SOURCE_MAP.md").write_text(
        "# Source Map\n\n| Source ID | Original | Converted | Purpose | Status |\n"
        "|---|---|---|---|---|\n| - | - | - | - | - |\n",
        encoding="utf-8",
    )
    (tmp_path / "CONTEXT_INDEX.md").write_text(
        "# Context Index\n\n## Materials\n\n| # | Context File | Type | Purpose | Notes |\n"
        "|---|---|---|---|---|\n| - | - | - | - | - |\n",
        encoding="utf-8",
    )

    for directory in ["_context", "_sources", "_skills", "_versions", "_logs"]:
        (tmp_path / directory).mkdir()

    (tmp_path / "_logs" / "raw_input.md").write_text(
        "# Raw Input\n\nBuild a validated handoff workspace.\n",
        encoding="utf-8",
    )
    (tmp_path / "_logs" / "gap_analysis.json").write_text(
        (
            '{"blockers":[],"assumptions":[],"optional_items":[],'
            '"missing_materials":[],"targeted_questions":[],"readiness_score":100}'
        ),
        encoding="utf-8",
    )
    snapshot_dir = tmp_path / "_versions" / "2026-05-27_0900"
    snapshot_dir.mkdir()
    (snapshot_dir / "SNAPSHOT.md").write_text("# Snapshot\n", encoding="utf-8")
    state = ProjectState(
        project_name="validator-regression",
        display_name="Validator Regression",
        main_goal="Validate a handoff workspace.",
        phase=ProjectPhase.HANDOFF_READY,
        readiness=ReadinessSnapshot(score=100, can_build=True),
    )

    assert validate_workspace(tmp_path) == []

    report = run_validation_suite(tmp_path, state=state, requirements=_requirements())
    assert report.passed is True
    assert report.error_count == 0
