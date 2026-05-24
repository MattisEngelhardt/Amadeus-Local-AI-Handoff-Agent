from __future__ import annotations

import logging

from amadeus.models.requirements import FilePlaceholder, RequirementsModel

logger = logging.getLogger(__name__)


CANONICAL_HANDOFF_FILES = [
    ("CLAUDE.md", "Stateful brain for Claude Code and compatible executing agents"),
    ("AGENTS.md", "Concise Codex-compatible instructions"),
    ("MASTER_PROMPT.md", "Compiled task prompt for the executing agent"),
    ("PROJECT_BRIEF.md", "Short orientation and goal summary"),
    ("REQUIREMENTS.md", "Structured requirements and non-goals"),
    ("DECISIONS.md", "Decisions, assumptions, and rationale"),
    ("NEXT_STEPS.md", "Ordered execution plan"),
    ("CONTEXT_INDEX.md", "Navigation for converted context files"),
    ("SOURCE_MAP.md", "Traceability map from originals to context files"),
]


class RequirementsValidator:
    """Deterministic validator for Amadeus handoff workspace requirements."""

    def __init__(self, **_legacy_kwargs: object) -> None:
        pass

    def validate(
        self,
        original_transcript: str,
        requirements: RequirementsModel,
        max_iterations: int = 1,
    ) -> RequirementsModel:
        del max_iterations

        requirements.project_name = self._safe_project_name(requirements.project_name)
        requirements.project_type = "AI handoff workspace"
        requirements.dependencies = []

        if not requirements.specifications:
            requirements.specifications = [
                "Prepare a complete handoff workspace from the provided user input.",
                "Keep missing context visible instead of inventing details.",
            ]

        if not requirements.quality_criteria:
            requirements.quality_criteria = []

        required_quality = [
            "Preserve raw user intent and do not invent missing source material.",
            "Keep generated workspace file and folder names in English.",
            "Block or document assumptions when context is incomplete.",
            "The executing agent must read CLAUDE.md, AGENTS.md, and MASTER_PROMPT.md first.",
        ]
        for criterion in required_quality:
            if criterion not in requirements.quality_criteria:
                requirements.quality_criteria.append(criterion)

        existing = {file.file_path for file in requirements.files_to_create}
        for file_path, purpose in CANONICAL_HANDOFF_FILES:
            if file_path not in existing:
                requirements.files_to_create.append(
                    FilePlaceholder(file_path=file_path, purpose=purpose)
                )

        if original_transcript.strip():
            transcript_spec = "Original raw input is preserved in _logs/raw_input.md."
            if transcript_spec not in requirements.specifications:
                requirements.specifications.append(transcript_spec)

        return requirements

    def _safe_project_name(self, project_name: str) -> str:
        cleaned = project_name.strip().lower().replace("_", "-")
        allowed = []
        previous_dash = False
        for char in cleaned:
            if char.isalnum():
                allowed.append(char)
                previous_dash = False
            elif not previous_dash:
                allowed.append("-")
                previous_dash = True
        safe = "".join(allowed).strip("-")
        return safe or "amadeus-handoff-workspace"
