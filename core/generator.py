from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from amadeus.models.project import ProjectFileModel
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectState

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """Generates Amadeus handoff workspace files instead of production app code."""

    def __init__(self, **_legacy_kwargs: object) -> None:
        template_dir = Path(__file__).resolve().parents[1] / "docs" / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def generate_all_files(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None = None,
        readiness_report: str = "",
    ) -> list[ProjectFileModel]:
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        files = [
            ProjectFileModel(
                file_path="PROJECT_BRIEF.md",
                content=self._project_brief(requirements, now, state),
                purpose="Short project orientation",
            ),
            ProjectFileModel(
                file_path="MASTER_PROMPT.md",
                content=self._master_prompt(requirements, state),
                purpose="Compiled task prompt for the executing agent",
            ),
            ProjectFileModel(
                file_path="REQUIREMENTS.md",
                content=self._requirements(requirements),
                purpose="Structured requirements and non-goals",
            ),
            ProjectFileModel(
                file_path="DECISIONS.md",
                content=self._decisions(requirements, state),
                purpose="Decisions, assumptions, and rationale",
            ),
            ProjectFileModel(
                file_path="NEXT_STEPS.md",
                content=self._next_steps(requirements, state),
                purpose="Ordered execution plan",
            ),
            ProjectFileModel(
                file_path="CONTEXT_INDEX.md",
                content=self._context_index(state),
                purpose="Context navigation",
            ),
            ProjectFileModel(
                file_path="SOURCE_MAP.md",
                content=self._source_map(state),
                purpose="Source provenance map",
            ),
            ProjectFileModel(
                file_path="_logs/raw_input.md",
                content=self._raw_input_log(state),
                purpose="Raw user input placeholder",
            ),
            ProjectFileModel(
                file_path="_context/README.md",
                content="# Context\n\nConverted source material belongs in this folder.\n",
                purpose="Context folder marker",
            ),
            ProjectFileModel(
                file_path="_sources/README.md",
                content=(
                    "# Sources\n\n"
                    "Original user-provided files belong in this folder unchanged.\n"
                ),
                purpose="Sources folder marker",
            ),
            ProjectFileModel(
                file_path="_skills/README.md",
                content="# Skills\n\nOptional specialist execution instructions belong here.\n",
                purpose="Skills folder marker",
            ),
            ProjectFileModel(
                file_path="_versions/README.md",
                content="# Versions\n\nSnapshots of major workspace changes belong here.\n",
                purpose="Version folder marker",
            ),
        ]

        files.append(
            ProjectFileModel(
                file_path="CLAUDE.md",
                content=self._render_target_template("TARGET_CLAUDE_TEMPLATE.md", requirements),
                purpose="Stateful brain for Claude Code and compatible agents",
            )
        )
        files.append(
            ProjectFileModel(
                file_path="AGENTS.md",
                content=self._render_target_template("TARGET_AGENTS_TEMPLATE.md", requirements),
                purpose="Codex-compatible agent instructions",
            )
        )

        if readiness_report:
            files.append(
                ProjectFileModel(
                    file_path="_logs/readiness_gate.md",
                    content=readiness_report,
                    purpose="Readiness gate report captured before workspace build",
                )
            )

        return files

    def _render_target_template(self, template_name: str, requirements: RequirementsModel) -> str:
        constraints = "\n".join(f"- {item}" for item in requirements.quality_criteria)
        commands = "- No project build command is known yet.\n- Follow `NEXT_STEPS.md` first."
        template = self.jinja_env.get_template(template_name)
        rendered = template.render(
            PROJECT_NAME=requirements.display_name,
            PROJECT_GOAL=requirements.short_description,
            CONSTRAINTS=constraints or "- No explicit constraints were captured.",
            COMMANDS=commands,
        )
        return rendered.rstrip() + "\n"

    def _project_brief(
        self,
        requirements: RequirementsModel,
        generated_at: str,
        state: ProjectState | None,
    ) -> str:
        readiness = (
            f"Readiness score: {state.readiness.score}/100\n"
            f"State phase: {state.phase.value}\n"
            if state
            else ""
        )
        return f"""# {requirements.display_name}

Generated by Amadeus: {generated_at}
Workspace type: AI handoff workspace
{readiness}

## Goal

{requirements.short_description}

## Intended Handoff Targets

- Codex
- Claude Code
- Antigravity

## Current State

This workspace contains the prepared context and execution instructions.
The executing agent should not treat Amadeus as having completed the final
project task.
"""

    def _master_prompt(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None,
    ) -> str:
        specs = self._bullet_list(requirements.specifications)
        quality = self._bullet_list(requirements.quality_criteria)
        open_questions = self._bullet_list(state.open_questions if state else [])
        return f"""# Master Prompt

## Context

Amadeus prepared this handoff workspace from the user's raw project input.

## Role

You are the executing agent. Complete the task described here using the
workspace files as the source of truth.

## Goal

{requirements.short_description}

## Requirements

{specs}

## Non-Goals

- Do not invent missing source material.
- Do not ignore open questions or documented assumptions.
- Do not delete `_sources/`, `_context/`, `_logs/`, or `_versions/`.

## Working Materials

- Use `_context/` for converted source material.
- Use `_sources/` only when original files are needed.
- Use `SOURCE_MAP.md` before relying on source material.

## Output Expectations

- Complete the user's final task in the target project context.
- Keep decisions traceable in `DECISIONS.md`.
- Preserve the quality criteria below.

## Working Method

- Read `CLAUDE.md` and `AGENTS.md`.
- Follow `NEXT_STEPS.md` in order.
- Ask the user when a blocker cannot be resolved from workspace files.

## Step-by-Step Plan

- Review project brief and requirements.
- Inspect context and source map.
- Resolve blockers or document approved assumptions.
- Execute the task.
- Run verification.
- Summarize outcomes and residual risks.

## Quality Criteria

{quality}

## Risks

- Source material may be incomplete until `_sources/` and `_context/` are populated.
- Open questions must not be hidden.

## Open Questions

{open_questions}
"""

    def _requirements(self, requirements: RequirementsModel) -> str:
        return f"""# Requirements

## Project

- Name: {requirements.display_name}
- Folder: `{requirements.project_name}`
- Type: {requirements.project_type}

## Specifications

{self._bullet_list(requirements.specifications)}

## Quality Criteria

{self._bullet_list(requirements.quality_criteria)}

## Planned Handoff Files

{self._file_table(requirements)}
"""

    def _decisions(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None,
    ) -> str:
        del requirements
        assumptions = self._gap_summary(state, "assumption")
        blockers = self._gap_summary(state, "blocker")
        approval = (
            f"- Readiness gate approval note: {state.approval_note}"
            if state and state.approval_note
            else "- No readiness waiver was recorded."
        )
        return f"""# Decisions

## Confirmed Decisions

- Amadeus prepares the handoff workspace; it does not execute the final task.
- Workspace files and folders use English names.
- Original sources are preserved under `_sources/`.
- Converted context belongs under `_context/`.

## Assumptions

{assumptions}

## Open Blockers

{blockers}

## Readiness Approval

{approval}
"""

    def _next_steps(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None,
    ) -> str:
        del requirements
        blocker_step = (
            "- Review waived readiness blockers in `DECISIONS.md` before execution.\n"
            if state and any(gap.category == "blocker" for gap in state.gaps)
            else ""
        )
        return f"""# Next Steps

{blocker_step}- Read `CLAUDE.md`, `AGENTS.md`, and `MASTER_PROMPT.md`.
- Check `SOURCE_MAP.md` and `CONTEXT_INDEX.md`.
- Add or convert missing source materials into `_sources/` and `_context/`.
- Resolve blockers documented in `DECISIONS.md`.
- Execute the final user task.
- Run verification appropriate to the task.
- Record important scope decisions in `DECISIONS.md`.
"""

    def _context_index(self, state: ProjectState | None) -> str:
        rows = ["| Context File | Source ID | Purpose | Notes |", "|---|---|---|---|"]
        if state:
            for material in state.materials:
                if material.context_path:
                    notes = "; ".join(material.extraction_notes) or material.status
                    rows.append(
                        "| "
                        f"`{material.context_path}` | {material.source_id} | "
                        f"{material.purpose or 'Source context'} | {notes} |"
                    )

        if len(rows) > 2:
            return "# Context Index\n\n" + "\n".join(rows) + "\n"

        return """# Context Index

No converted source files were registered during initial workspace generation.

Add entries in this format:

| Context File | Source ID | Purpose | Notes |
|---|---|---|---|
"""

    def _source_map(self, state: ProjectState | None) -> str:
        rows = [
            "| Source ID | Original Source | Converted Context | Purpose | Referenced By |",
            "|---|---|---|---|---|",
        ]
        if state:
            for material in state.materials:
                rows.append(
                    "| "
                    f"{material.source_id} | `{material.original_path}` | "
                    f"`{material.context_path or 'not converted'}` | "
                    f"{material.purpose or 'Source material'} | MASTER_PROMPT.md |"
                )

        if len(rows) > 2:
            return "# Source Map\n\n" + "\n".join(rows) + "\n"

        return """# Source Map

No original sources were registered during initial workspace generation.

Add entries in this format:

| Source ID | Original Source | Converted Context | Purpose | Referenced By |
|---|---|---|---|---|
"""

    def _raw_input_log(self, state: ProjectState | None) -> str:
        if not state or not state.raw_inputs:
            return "# Raw Input\n\nRaw voice or text input is recorded here by Amadeus.\n"

        sections = ["# Raw Input"]
        for item in state.raw_inputs:
            sections.append(
                f"## {item.input_id}\n\n"
                f"- Channel: {item.channel}\n"
                f"- Kind: {item.kind}\n"
                f"- Received: {item.received_at}\n\n"
                f"{item.raw_text.strip() or '_No raw text captured._'}"
            )
        return "\n\n".join(sections) + "\n"

    def _bullet_list(self, items: list[str]) -> str:
        if not items:
            return "- None captured."
        return "\n".join(f"- {item}" for item in items)

    def _gap_summary(self, state: ProjectState | None, category: str) -> str:
        if not state:
            return "- None recorded."

        gaps = [gap for gap in state.gaps if gap.category == category]
        if not gaps:
            return "- None recorded."

        return "\n".join(
            f"- {gap.title} ({gap.status}): {gap.detail}" for gap in gaps
        )

    def _file_table(self, requirements: RequirementsModel) -> str:
        rows = ["| File | Purpose |", "|---|---|"]
        for file in requirements.files_to_create:
            path = os.path.normpath(file.file_path).replace("\\", "/")
            rows.append(f"| `{path}` | {file.purpose} |")
        return "\n".join(rows)
