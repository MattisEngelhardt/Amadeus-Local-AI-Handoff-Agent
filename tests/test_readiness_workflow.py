from __future__ import annotations

import json
from pathlib import Path

from amadeus.core.validator import RequirementsValidator
from amadeus.core.workflow import prepare_handoff_workspace
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectPhase


def _requirements(project_name: str = "readiness-workspace") -> RequirementsModel:
    requirements = RequirementsModel(
        project_name=project_name,
        display_name="Readiness Workspace",
        short_description="Prepare a handoff workspace for a command line study tool.",
        project_type="AI handoff workspace",
        tech_stack=["Codex", "Claude Code"],
        dependencies=[],
        specifications=["Build a CLI tool handoff workspace."],
        quality_criteria=["Keep source gaps visible."],
        files_to_create=[],
    )
    return RequirementsValidator().validate("raw input", requirements)


def test_prepare_handoff_workspace_writes_state_and_readiness_logs(tmp_path):
    result = prepare_handoff_workspace(
        _requirements(),
        raw_text="Build a CLI tool that summarizes study notes into a report.",
        output_dir=str(tmp_path),
    )

    assert result.built is True
    assert result.blocked is False
    assert result.state.phase == ProjectPhase.HANDOFF_READY

    project_path = Path(result.project_path)
    assert (project_path / "MASTER_PROMPT.md").exists()
    assert (project_path / "_logs" / "amadeus_state.json").exists()
    assert (project_path / "_logs" / "gap_analysis.json").exists()
    assert (project_path / "_logs" / "readiness_gate.md").exists()

    state_payload = json.loads((project_path / "_logs" / "amadeus_state.json").read_text())
    assert state_payload["readiness"]["score"] > 0
    assert state_payload["phase"] == "handoff_ready"


def test_prepare_handoff_workspace_blocks_when_referenced_material_is_missing(tmp_path):
    result = prepare_handoff_workspace(
        _requirements("missing-material-workspace"),
        raw_text="Build a report from the attached PDF file.",
        output_dir=str(tmp_path),
    )

    assert result.built is False
    assert result.blocked is True
    assert result.state.phase == ProjectPhase.READINESS_REVIEW
    assert result.state.open_blockers()

    project_path = Path(result.project_path)
    assert not (project_path / "MASTER_PROMPT.md").exists()
    assert (project_path / "_logs" / "amadeus_state.json").exists()
    readiness_report = (project_path / "_logs" / "readiness_gate.md").read_text()
    assert "Build status: Blocked" in readiness_report
    assert "Referenced materials are missing" in readiness_report


def test_prepare_handoff_workspace_can_build_with_documented_readiness_approval(tmp_path):
    result = prepare_handoff_workspace(
        _requirements("approved-material-workspace"),
        raw_text="Build a report from the attached PDF file.",
        output_dir=str(tmp_path),
        approve_readiness=True,
        approval_note="Proceed with text-only workspace until the PDF is supplied later.",
    )

    assert result.built is True
    assert result.blocked is False
    assert result.state.phase == ProjectPhase.HANDOFF_READY
    assert not result.state.open_blockers()
    assert result.state.readiness_approved is True

    project_path = Path(result.project_path)
    decisions = (project_path / "DECISIONS.md").read_text()
    assert "Referenced materials are missing (waived)" in decisions
    assert "Proceed with text-only workspace" in decisions
