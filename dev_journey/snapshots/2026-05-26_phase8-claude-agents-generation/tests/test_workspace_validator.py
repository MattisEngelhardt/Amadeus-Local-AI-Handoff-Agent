from __future__ import annotations

from amadeus.core.workspace_validator import (
    AGENTS_REQUIRED_SECTIONS,
    CLAUDE_REQUIRED_SECTIONS,
    validate_agents_md_anatomy,
    validate_claude_md_anatomy,
    validate_workspace,
)


def _complete_claude_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in CLAUDE_REQUIRED_SECTIONS)
    return f"# Project Brain\n\n{sections}\n"


def _complete_agents_md() -> str:
    sections = "\n\n".join(f"## {section}\n\nContent." for section in AGENTS_REQUIRED_SECTIONS)
    return f"# Agent Instructions\n\n{sections}\n"


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
