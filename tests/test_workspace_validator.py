from __future__ import annotations

from pathlib import Path
from amadeus.core.workspace_validator import validate_workspace

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

def test_validate_workspace_passes_valid_workspace(tmp_path):
    for f in ["CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md", "PROJECT_BRIEF.md", "REQUIREMENTS.md", "DECISIONS.md", "NEXT_STEPS.md", "CONTEXT_INDEX.md", "SOURCE_MAP.md"]:
        (tmp_path / f).write_text("Content", encoding="utf-8")

    for d in ["_context", "_sources", "_skills", "_versions", "_logs"]:
        (tmp_path / d).mkdir()

    (tmp_path / "SOURCE_MAP.md").write_text("`_sources/test.txt` `_context/test.md`", encoding="utf-8")
    (tmp_path / "_sources" / "test.txt").write_text("test", encoding="utf-8")
    (tmp_path / "_context" / "test.md").write_text("test", encoding="utf-8")

    errors = validate_workspace(tmp_path)
    assert not errors
