from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any, Literal

from amadeus.models.tools import ActionRecord
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ProjectPhase(str, Enum):
    CONTEXT_COLLECTION = "context_collection"
    READINESS_REVIEW = "readiness_review"
    WORKSPACE_BUILD = "workspace_build"
    HANDOFF_READY = "handoff_ready"


class RawInputRecord(BaseModel):
    input_id: str
    channel: str = "cli"
    kind: Literal[
        "text",
        "audio",
        "telegram_text",
        "telegram_voice",
        "file",
        "link",
        "image",
        "old_prompt",
        "correction",
    ] = "text"
    received_at: str = Field(default_factory=utc_now_iso)
    raw_text: str = ""
    file_path: str = ""
    content_digest: str = ""
    is_duplicate: bool = False
    duplicate_of: str = ""
    notes: list[str] = Field(default_factory=list)


class TranscriptRecord(BaseModel):
    transcript_id: str
    input_id: str
    raw_transcript_path: str = "_logs/raw_input.md"
    cleaned_transcript_path: str = ""
    language: str = "de"
    uncertain_terms: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)



class LinkRecord(BaseModel):
    link_id: str
    url: str
    purpose: str = ""
    status: Literal["registered", "processed", "failed"] = "registered"
    notes: list[str] = Field(default_factory=list)


class DecisionRecord(BaseModel):
    decision_id: str
    summary: str
    rationale: str = ""
    approved_by_user: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    source_ids: list[str] = Field(default_factory=list)


class GapItem(BaseModel):
    gap_id: str
    category: Literal["blocker", "assumption", "optional"]
    title: str
    detail: str
    question: str = ""
    status: Literal["open", "recorded", "resolved", "waived"] = "open"
    source_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)


class PromptVersionRecord(BaseModel):
    version: int
    path: str = "MASTER_PROMPT.md"
    created_at: str = Field(default_factory=utc_now_iso)
    notes: str = ""


class WorkspacePlan(BaseModel):
    target_path: str = ""
    executing_agents: list[str] = Field(
        default_factory=lambda: ["Codex", "Claude Code", "Antigravity"]
    )
    planned_files: list[str] = Field(default_factory=list)
    planned_directories: list[str] = Field(default_factory=list)
    skills_to_include: list[str] = Field(default_factory=list)


class ReadinessSnapshot(BaseModel):
    score: int = 0
    can_build: bool = False
    approval_required: bool = False
    open_blockers: list[str] = Field(default_factory=list)
    recorded_assumptions: list[str] = Field(default_factory=list)
    optional_items: list[str] = Field(default_factory=list)
    missing_materials: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now_iso)


class MaterialRecord(BaseModel):
    source_id: str
    original_path: str
    context_path: str = ""
    material_type: str = "unknown"
    purpose: str = ""
    status: Literal["registered", "converted", "failed", "partial"] = "registered"
    extraction_notes: list[str] = Field(default_factory=list)
    extraction_confidence: float = 1.0
    page_count: int | None = None


class ProjectRegistryEntry(BaseModel):
    project_name: str
    display_name: str
    project_path: str
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    phase: ProjectPhase = ProjectPhase.CONTEXT_COLLECTION
    readiness_score: int = 0
    is_active: bool = False
    is_archived: bool = False
    input_count: int = 0


class ProjectState(BaseModel):
    schema_version: int = 1
    project_name: str
    display_name: str
    main_goal: str
    phase: ProjectPhase = ProjectPhase.CONTEXT_COLLECTION
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    target_path: str = ""
    executing_agent: str = "Codex"
    requirements: dict[str, Any] = Field(default_factory=dict)
    raw_inputs: list[RawInputRecord] = Field(default_factory=list)
    transcripts: list[TranscriptRecord] = Field(default_factory=list)
    materials: list[MaterialRecord] = Field(default_factory=list)
    links: list[LinkRecord] = Field(default_factory=list)
    decisions: list[DecisionRecord] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    prompt_versions: list[PromptVersionRecord] = Field(default_factory=list)
    workspace_plan: WorkspacePlan = Field(default_factory=WorkspacePlan)
    readiness: ReadinessSnapshot = Field(default_factory=ReadinessSnapshot)
    action_log: list[ActionRecord] = Field(default_factory=list)
    readiness_approved: bool = False
    approval_note: str = ""

    def transition_to(self, phase: ProjectPhase) -> None:
        self.phase = phase
        self.touch()

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def open_blockers(self) -> list[GapItem]:
        return [
            gap
            for gap in self.gaps
            if gap.category == "blocker" and gap.status not in {"resolved", "waived"}
        ]

    def recorded_assumptions(self) -> list[GapItem]:
        return [gap for gap in self.gaps if gap.category == "assumption"]
