from __future__ import annotations

from amadeus.core.versioning import create_workspace_snapshot


def test_create_workspace_snapshot_copies_canonical_files(tmp_path):
    project = tmp_path / "my_project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("Claude content", encoding="utf-8")
    (project / "AGENTS.md").write_text("Agents content", encoding="utf-8")

    snapshot_dir = create_workspace_snapshot(project, "Initial snapshot")

    assert snapshot_dir.exists()
    assert (snapshot_dir / "CLAUDE.md").read_text(encoding="utf-8") == "Claude content"
    assert (snapshot_dir / "AGENTS.md").read_text(encoding="utf-8") == "Agents content"
    assert not (snapshot_dir / "PROJECT_BRIEF.md").exists()

    snapshot_info = (snapshot_dir / "SNAPSHOT.md").read_text(encoding="utf-8")
    assert "Reason: Initial snapshot" in snapshot_info
