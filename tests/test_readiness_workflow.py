from __future__ import annotations

import json
from pathlib import Path

from amadeus.core.validation_suite import VALIDATOR_NAMES
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
    assert (project_path / "_logs" / "validation_report.md").exists()
    assert (project_path / "_logs" / "validation_report.json").exists()

    state_payload = json.loads((project_path / "_logs" / "amadeus_state.json").read_text())
    assert state_payload["readiness"]["score"] > 0
    assert state_payload["phase"] == "handoff_ready"

    validation_payload = json.loads(
        (project_path / "_logs" / "validation_report.json").read_text()
    )
    assert validation_payload["validators_run"] == VALIDATOR_NAMES


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


def test_workflow_does_not_treat_future_csv_inputs_as_missing_materials(tmp_path):
    result = prepare_handoff_workspace(
        _requirements("csv-tool-workspace"),
        raw_text=(
            "Build a CLI tool that processes CSV files and generates "
            "summary reports with charts."
        ),
        output_dir=str(tmp_path),
    )

    assert result.built is True
    assert result.blocked is False
    assert not result.state.open_blockers()


def test_workflow_with_text_material_ingests_and_builds(tmp_path):
    source_file = tmp_path / "notes.txt"
    source_file.write_text("Detailed requirements note.", encoding="utf-8")

    result = prepare_handoff_workspace(
        _requirements("material-workspace"),
        raw_text="Build the system based on the attached files.",
        output_dir=str(tmp_path),
        source_files=[source_file],
    )

    assert result.built is True
    assert result.blocked is False
    assert len(result.state.materials) == 1
    assert result.state.materials[0].status == "converted"

    project_path = Path(result.project_path)
    assert (project_path / "_sources" / "notes.txt").exists()

    # context filename is slugified, let's just check if any .md file is there
    context_files = list((project_path / "_context").glob("*.md"))
    assert len([f for f in context_files if f.name != "README.md"]) == 1

    source_map = (project_path / "SOURCE_MAP.md").read_text(encoding="utf-8")
    assert "notes.txt" in source_map
    assert "converted" in source_map


def test_workflow_with_failed_material_creates_blocker(tmp_path):
    # Pass a file that does not exist
    missing_file = tmp_path / "does_not_exist.txt"

    result = prepare_handoff_workspace(
        _requirements("failed-material-workspace"),
        raw_text="Build using the attached notes.",
        output_dir=str(tmp_path),
        source_files=[missing_file],
    )

    assert result.built is False
    assert result.blocked is True
    assert any("does_not_exist.txt" in b.title for b in result.state.open_blockers())
    assert result.state.materials[0].status == "failed"


def test_workflow_with_unsupported_material_creates_blocker(tmp_path):
    unsupported_file = tmp_path / "archive.zip"
    unsupported_file.write_bytes(b"PK\x03\x04")

    result = prepare_handoff_workspace(
        _requirements("unsupported-material-workspace"),
        raw_text="See the attached zip archive.",
        output_dir=str(tmp_path),
        source_files=[unsupported_file],
    )

    assert result.built is False
    assert result.blocked is True
    assert result.state.materials[0].status == "failed"
    assert "Unsupported material type '.zip'" in result.state.materials[0].extraction_notes[0]

