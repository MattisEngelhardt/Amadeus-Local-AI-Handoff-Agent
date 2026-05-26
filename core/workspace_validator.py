from __future__ import annotations

import re
from pathlib import Path


def validate_workspace(project_path: Path | str) -> list[str]:
    project_path = Path(project_path)
    errors = []

    # 1. Check for canonical files
    canonical_files = [
        "CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md",
        "PROJECT_BRIEF.md", "REQUIREMENTS.md", "DECISIONS.md",
        "NEXT_STEPS.md", "CONTEXT_INDEX.md", "SOURCE_MAP.md"
    ]
    for fname in canonical_files:
        if not (project_path / fname).exists():
            errors.append(f"Missing canonical file: {fname}")

    # 2. Check for canonical directories
    canonical_dirs = ["_context", "_sources", "_skills", "_versions", "_logs"]
    for dname in canonical_dirs:
        if not (project_path / dname).is_dir():
            errors.append(f"Missing canonical directory: {dname}")

    # 3. Check if CLAUDE.md is not empty
    claude_md = project_path / "CLAUDE.md"
    if claude_md.exists() and len(claude_md.read_text(encoding="utf-8").strip()) == 0:
        errors.append("CLAUDE.md is empty")

    # 4. English file/folder names (basic heuristic: no standard German indicators like umlauts, or specifically German words if we want to be strict, but keeping it simple: no non-ASCII in root)
    for child in project_path.iterdir():
        if not re.match(r"^[a-zA-Z0-9_.-]+$", child.name):
            errors.append(f"Non-standard characters in root name: {child.name}")

    # 5. SOURCE_MAP.md references
    source_map = project_path / "SOURCE_MAP.md"
    if source_map.exists():
        content = source_map.read_text(encoding="utf-8")
        # Extract paths in backticks under the Original/Converted columns
        # E.g. `_sources/file.txt`
        for match in re.finditer(r"`(_sources/[^`]+)`", content):
            src_file = project_path / match.group(1)
            if not src_file.exists():
                errors.append(f"SOURCE_MAP.md references missing source file: {match.group(1)}")
        for match in re.finditer(r"`(_context/[^`]+)`", content):
            ctx_file = project_path / match.group(1)
            if not ctx_file.exists():
                errors.append(f"SOURCE_MAP.md references missing context file: {match.group(1)}")

    return errors
