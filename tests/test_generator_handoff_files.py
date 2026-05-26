from __future__ import annotations

from amadeus.core.generator import ProjectGenerator
from amadeus.core.workspace_validator import (
    AGENTS_REQUIRED_SECTIONS,
    CLAUDE_REQUIRED_SECTIONS,
)
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import (
    DecisionRecord,
    GapItem,
    MaterialRecord,
    ProjectPhase,
    ProjectState,
    PromptVersionRecord,
    ReadinessSnapshot,
    WorkspacePlan,
)


def _requirements() -> RequirementsModel:
    return RequirementsModel(
        project_name="phase8-handoff",
        display_name="Phase 8 Handoff",
        short_description="Build a CSV reporting CLI handoff workspace.",
        project_type="AI handoff workspace",
        tech_stack=["Python", "Typer"],
        dependencies=["pandas", "matplotlib"],
        specifications=[
            "Parse CSV files from an input directory.",
            "Generate summary tables and chart outputs.",
            "Document all verification steps.",
        ],
        quality_criteria=[
            "Source claims must cite provided material.",
            "The CLI must fail clearly on malformed CSV input.",
        ],
        files_to_create=[],
    )


def _state() -> ProjectState:
    return ProjectState(
        project_name="phase8-handoff",
        display_name="Phase 8 Handoff",
        main_goal="Build a CSV reporting CLI handoff workspace.",
        phase=ProjectPhase.WORKSPACE_BUILD,
        target_path="C:/tmp/phase8-handoff",
        requirements={},
        materials=[
            MaterialRecord(
                source_id="source-001",
                original_path="_sources/client-brief.md",
                context_path="_context/source-001-client-brief.md",
                material_type="md",
                purpose="Client requirements brief",
                status="converted",
                extraction_notes=["Plain text material ingested as UTF-8."],
            )
        ],
        decisions=[
            DecisionRecord(
                decision_id="decision-001",
                summary="Use local handoff files as the only source of truth.",
                rationale="The workspace must be self-contained.",
                approved_by_user=True,
            )
        ],
        gaps=[
            GapItem(
                gap_id="gap-001",
                category="assumption",
                title="Charts can use a standard static image format",
                detail="No preferred chart file format was provided.",
                status="recorded",
            ),
            GapItem(
                gap_id="gap-002",
                category="blocker",
                title="No real CSV fixture supplied",
                detail="The executing agent may need to create representative fixtures.",
                status="waived",
            ),
        ],
        open_questions=["Should chart output be PNG or SVG?"],
        prompt_versions=[
            PromptVersionRecord(version=2, path="MASTER_PROMPT.md", notes="Phase 8 test")
        ],
        workspace_plan=WorkspacePlan(
            executing_agents=["Codex", "Claude Code"],
            planned_files=["CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md"],
            planned_directories=["_context", "_sources", "_skills", "_versions", "_logs"],
            skills_to_include=["csv-reporting"],
        ),
        readiness=ReadinessSnapshot(score=91, can_build=True),
        readiness_approved=True,
        approval_note="User approved build with a documented fixture assumption.",
    )


def test_generator_produces_rich_claude_and_agents_files():
    generated_files = ProjectGenerator().generate_all_files(_requirements(), state=_state())
    by_path = {file.file_path: file.content for file in generated_files}

    claude_md = by_path["CLAUDE.md"]
    agents_md = by_path["AGENTS.md"]

    for section in CLAUDE_REQUIRED_SECTIONS:
        assert section in claude_md

    for section in AGENTS_REQUIRED_SECTIONS:
        assert section in agents_md
    assert "Implementation Priorities" in agents_md

    assert "Phase 8 Handoff" in claude_md
    assert "Phase 8 Handoff" in agents_md
    assert "Source claims must cite provided material." in claude_md
    assert "Source claims must cite provided material." in agents_md
    assert "The CLI must fail clearly on malformed CSV input." in claude_md
    assert "Readiness score: 91/100" in claude_md
    assert "SOURCE_MAP.md#source-map" in claude_md
    assert "CONTEXT_INDEX.md#materials" in claude_md
