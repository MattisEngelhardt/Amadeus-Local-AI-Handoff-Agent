from __future__ import annotations

import hashlib
import os
from pathlib import Path

from amadeus.core.scaffolder import CANONICAL_DIRECTORIES
from amadeus.core.validator import CANONICAL_HANDOFF_FILES
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import (
    ProjectState,
    PromptVersionRecord,
    RawInputRecord,
    TranscriptRecord,
    WorkspacePlan,
)

STATE_FILE = "amadeus_state.json"
GAP_ANALYSIS_FILE = "gap_analysis.json"
READINESS_FILE = "readiness_gate.md"


class ProjectStateStore:
    """Creates, saves, and loads Amadeus project state."""

    def create_for_text(
        self,
        requirements: RequirementsModel,
        raw_text: str,
        target_path: str,
        channel: str = "cli",
        input_kind: str = "text",
        transcript_language: str = "de",
    ) -> ProjectState:
        input_id = self._stable_id("input", channel, raw_text)
        planned_files = [file_path for file_path, _purpose in CANONICAL_HANDOFF_FILES]

        for file in requirements.files_to_create:
            if file.file_path not in planned_files:
                planned_files.append(file.file_path)

        state = ProjectState(
            project_name=requirements.project_name,
            display_name=requirements.display_name,
            main_goal=requirements.short_description,
            target_path=target_path,
            executing_agent="Codex",
            requirements=requirements.model_dump(),
            raw_inputs=[
                RawInputRecord(
                    input_id=input_id,
                    channel=channel,
                    kind=input_kind,  # type: ignore[arg-type]
                    raw_text=raw_text,
                    content_digest=self._stable_id("digest", raw_text),
                )
            ],
            workspace_plan=WorkspacePlan(
                target_path=target_path,
                planned_files=planned_files,
                planned_directories=CANONICAL_DIRECTORIES,
            ),
            prompt_versions=[
                PromptVersionRecord(
                    version=1,
                    path="MASTER_PROMPT.md",
                    notes="Initial master prompt generated from captured context.",
                )
            ],
        )

        if input_kind in {"audio", "telegram_voice"}:
            state.transcripts.append(
                TranscriptRecord(
                    transcript_id=self._stable_id("transcript", input_id),
                    input_id=input_id,
                    language=transcript_language,
                )
            )

        return state

    def save(self, state: ProjectState, project_path: str) -> Path:
        logs_dir = Path(project_path) / "_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        state.touch()
        path = logs_dir / STATE_FILE
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        return path

    def save_gap_analysis(self, gap_analysis: object, project_path: str) -> Path:
        logs_dir = Path(project_path) / "_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        path = logs_dir / GAP_ANALYSIS_FILE
        if hasattr(gap_analysis, "model_dump_json"):
            content = gap_analysis.model_dump_json(indent=2)
        else:
            content = str(gap_analysis)
        path.write_text(content, encoding="utf-8")
        return path

    def save_readiness_report(self, report_markdown: str, project_path: str) -> Path:
        logs_dir = Path(project_path) / "_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        path = logs_dir / READINESS_FILE
        path.write_text(report_markdown, encoding="utf-8")
        return path

    def load(self, path: str) -> ProjectState:
        target = Path(path)
        if target.is_dir():
            target = target / "_logs" / STATE_FILE
        return ProjectState.model_validate_json(target.read_text(encoding="utf-8"))

    def expected_project_path(self, base_output_dir: str, project_name: str) -> str:
        return os.path.abspath(os.path.join(base_output_dir, project_name))

    def _stable_id(self, *parts: str) -> str:
        digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
        return digest
