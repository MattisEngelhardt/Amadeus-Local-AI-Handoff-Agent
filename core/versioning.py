from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def create_workspace_snapshot(
    project_path: Path | str,
    reason: str,
    files_to_snapshot: list[str] | None = None,
) -> Path:
    project_path = Path(project_path)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    snapshot_dir = project_path / "_versions" / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    target_files = files_to_snapshot or [
        "CLAUDE.md",
        "AGENTS.md",
        "MASTER_PROMPT.md",
        "PROJECT_BRIEF.md",
        "REQUIREMENTS.md",
        "DECISIONS.md",
    ]

    for fname in target_files:
        src = project_path / fname
        if src.exists():
            shutil.copy2(src, snapshot_dir / fname)

    (snapshot_dir / "SNAPSHOT.md").write_text(
        f"# Snapshot {timestamp}\n\nReason: {reason}\n", encoding="utf-8"
    )
    return snapshot_dir
