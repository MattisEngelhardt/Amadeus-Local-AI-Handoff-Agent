from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvalCaseInput(BaseModel):
    """What Amadeus receives."""

    raw_text: str
    source_files: list[str] = Field(default_factory=list)
    # Relative paths within the case directory for fixture files.
    # The runner copies them to tmp_path before calling the pipeline.
    approve_readiness: bool = False
    approval_note: str = ""
    project_name: str = "eval-project"


class EvalCaseExpectation(BaseModel):
    """What the eval case expects Amadeus to produce."""

    should_build: bool
    should_block: bool = False
    min_readiness_score: int = 0
    max_readiness_score: int = 100
    expected_blocker_keywords: list[str] = Field(default_factory=list)
    expected_assumption_keywords: list[str] = Field(default_factory=list)
    expected_material_count: int = 0
    expected_material_statuses: list[str] = Field(default_factory=list)
    # e.g. ["converted", "converted"] or ["converted", "failed"]
    expected_generated_files: list[str] = Field(
        default_factory=lambda: [
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
    )
    expected_validation_passed: bool = True
    source_map_must_contain: list[str] = Field(default_factory=list)
    # Strings that must appear in SOURCE_MAP.md


class EvalCase(BaseModel):
    """One complete evaluation scenario."""

    case_id: str
    title: str
    description: str
    category: Literal[
        "text_only",
        "material",
        "voice",
        "missing_context",
        "contradiction",
        "handoff_target",
        "academic",
    ]
    input: EvalCaseInput
    expectation: EvalCaseExpectation


class EvalScorecard(BaseModel):
    """Scores for one eval case run."""

    case_id: str
    passed: bool
    requirement_extraction: float = 0.0  # 0.0–1.0
    blocker_detection: float = 0.0
    assumption_discipline: float = 0.0
    readiness_score_accuracy: float = 0.0
    source_map_completeness: float = 0.0
    prompt_section_completeness: float = 0.0
    workspace_structure: float = 0.0
    validation_status: float = 0.0
    overall: float = 0.0
    errors: list[str] = Field(default_factory=list)


class EvalRunReport(BaseModel):
    """Summary of a full eval run."""

    mode: Literal["deterministic", "local_model"]
    timestamp: str
    commit_hash: str = ""
    cases_run: int
    cases_passed: int
    cases_failed: int
    average_score: float
    scorecards: list[EvalScorecard]
