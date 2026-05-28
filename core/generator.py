from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path

from amadeus.models.project import ProjectFileModel
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectState
from jinja2 import Environment, FileSystemLoader

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
                file_path="_logs/build_log.md",
                content=self._build_log(state, readiness_report, now),
                purpose="Protocol of the workspace build process",
            ),
            ProjectFileModel(
                file_path="_context/README.md",
                content="# Context\n\nConverted source material belongs in this folder.\n",
                purpose="Context folder marker",
            ),
            ProjectFileModel(
                file_path="_sources/README.md",
                content=(
                    "# Sources\n\nOriginal user-provided files belong in this folder unchanged.\n"
                ),
                purpose="Sources folder marker",
            ),
            ProjectFileModel(
                file_path="_skills/README.md",
                content=self._skills_readme(state),
                purpose="Skills folder marker",
            ),
            ProjectFileModel(
                file_path="_versions/README.md",
                content="# Versions\n\nSnapshots of major workspace changes belong here.\n",
                purpose="Version folder marker",
            ),
        ]

        claude_file = ProjectFileModel(
            file_path="CLAUDE.md",
            content="",
            purpose="Stateful brain for Claude Code and compatible agents",
        )
        agents_file = ProjectFileModel(
            file_path="AGENTS.md",
            content="",
            purpose="Codex-compatible agent instructions",
        )
        template_files = [*files, claude_file, agents_file]
        claude_file.content = self._render_target_template(
            "TARGET_CLAUDE_TEMPLATE.md",
            requirements,
            state=state,
            generated_files=template_files,
            generated_at=now,
        )
        agents_file.content = self._render_target_template(
            "TARGET_AGENTS_TEMPLATE.md",
            requirements,
            state=state,
            generated_files=template_files,
            generated_at=now,
        )
        files.extend([claude_file, agents_file])

        if readiness_report:
            files.append(
                ProjectFileModel(
                    file_path="_logs/readiness_gate.md",
                    content=readiness_report,
                    purpose="Readiness gate report captured before workspace build",
                )
            )

        return files

    def _render_target_template(
        self,
        template_name: str,
        requirements: RequirementsModel,
        state: ProjectState | None = None,
        generated_files: list[ProjectFileModel] | None = None,
        generated_at: str | None = None,
    ) -> str:
        template = self.jinja_env.get_template(template_name)
        rendered = template.render(
            PROJECT_NAME=requirements.display_name,
            PROJECT_GOAL=requirements.short_description,
            CONSTRAINTS=self._constraints(requirements, state),
            COMMANDS=self._commands(state),
            GENERATED_AT=generated_at or dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            READINESS_SCORE=self._readiness_score(state),
            READINESS_CAN_BUILD=self._readiness_can_build(state),
            PHASE=state.phase.value if state else "unknown",
            APPROVAL_NOTE=(
                state.approval_note
                if state and state.approval_note
                else "No readiness waiver was recorded."
            ),
            FILE_MAP_TABLE=self._file_map_table(generated_files),
            QUICKLINKS=self._quicklinks(),
            SKILLS_LIST=self._skills_list(state),
            QUALITY_CRITERIA=self._bullet_list(requirements.quality_criteria),
            OPEN_QUESTIONS=self._bullet_list(state.open_questions if state else []),
            OPEN_BLOCKERS=self._gap_summary(state, "blocker"),
            ASSUMPTIONS=self._gap_summary(state, "assumption"),
            DECISIONS_SUMMARY=self._decisions_summary(state),
            MATERIALS_SUMMARY=self._materials_summary(state),
            NEXT_STEPS_CONTENT=self._next_steps_content(requirements, state),
            EXECUTING_AGENTS=self._bullet_list(self._executing_agents(state)),
            EXECUTING_AGENTS_INLINE=", ".join(self._executing_agents(state)),
            TECH_STACK=self._bullet_list(requirements.tech_stack),
            DEPENDENCIES=self._bullet_list(requirements.dependencies),
            SPECIFICATIONS=self._bullet_list(requirements.specifications),
            PROMPT_VERSION=self._prompt_version(state),
        )
        return rendered.rstrip() + "\n"

    def _constraints(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None,
    ) -> str:
        items = list(requirements.quality_criteria)

        if state:
            for decision in state.decisions:
                if decision.rationale:
                    items.append(f"Decision: {decision.summary} Rationale: {decision.rationale}")
                else:
                    items.append(f"Decision: {decision.summary}")

            for gap in state.gaps:
                if gap.category == "assumption":
                    items.append(f"Recorded assumption: {gap.title} - {gap.detail}")

        if not items:
            return "- No explicit constraints were captured."
        return self._bullet_list(items)

    def _commands(self, state: ProjectState | None) -> str:
        if state:
            plan_commands = getattr(state.workspace_plan, "commands", None)
            if plan_commands:
                return self._bullet_list(list(plan_commands))

        return (
            "- No explicit build, test, or lint command was captured by Amadeus.\n"
            "- Follow `NEXT_STEPS.md` first.\n"
            "- Add concrete verification commands to `DECISIONS.md` once the "
            "target project defines them."
        )

    def _readiness_score(self, state: ProjectState | None) -> str:
        return str(state.readiness.score) if state else "unknown"

    def _readiness_can_build(self, state: ProjectState | None) -> str:
        if not state:
            return "unknown"
        return "yes" if state.readiness.can_build else "no"

    def _file_map_table(self, generated_files: list[ProjectFileModel] | None) -> str:
        rows = ["| Path | Purpose | When To Read |", "|---|---|---|"]
        seen = set()

        directory_rows = [
            ("_context/", "AI-optimized Markdown context", "Before using source material"),
            (
                "_sources/",
                "Original user-provided materials",
                "Only when converted context is insufficient",
            ),
            ("_skills/", "Optional specialist execution rules", "When a listed skill is relevant"),
            (
                "_versions/",
                "Snapshots and fallback versions",
                "For rollback or historical comparison",
            ),
            ("_logs/", "Raw inputs, transcripts, and build logs", "For audit or debugging"),
        ]
        for path, purpose, when_to_read in directory_rows:
            rows.append(
                f"| `{path}` | {self._table_cell(purpose)} | {self._table_cell(when_to_read)} |"
            )
            seen.add(path)

        file_models = generated_files or self._default_file_models()
        for file_model in file_models:
            path = os.path.normpath(file_model.file_path).replace("\\", "/")
            if path in seen:
                continue
            seen.add(path)
            rows.append(
                f"| `{path}` | {self._table_cell(file_model.purpose)} | "
                f"{self._table_cell(self._when_to_read(path))} |"
            )

        return "\n".join(rows)

    def _default_file_models(self) -> list[ProjectFileModel]:
        return [
            ProjectFileModel(
                file_path="CLAUDE.md",
                content="",
                purpose="Stateful brain for Claude Code and compatible agents",
            ),
            ProjectFileModel(
                file_path="AGENTS.md",
                content="",
                purpose="Codex-compatible agent instructions",
            ),
            ProjectFileModel(
                file_path="MASTER_PROMPT.md",
                content="",
                purpose="Compiled task prompt for the executing agent",
            ),
            ProjectFileModel(
                file_path="PROJECT_BRIEF.md",
                content="",
                purpose="Short project orientation",
            ),
            ProjectFileModel(
                file_path="REQUIREMENTS.md",
                content="",
                purpose="Structured requirements and non-goals",
            ),
            ProjectFileModel(
                file_path="DECISIONS.md",
                content="",
                purpose="Decisions, assumptions, and rationale",
            ),
            ProjectFileModel(
                file_path="NEXT_STEPS.md",
                content="",
                purpose="Ordered execution plan",
            ),
            ProjectFileModel(
                file_path="CONTEXT_INDEX.md",
                content="",
                purpose="Context navigation",
            ),
            ProjectFileModel(
                file_path="SOURCE_MAP.md",
                content="",
                purpose="Source provenance map",
            ),
        ]

    def _when_to_read(self, path: str) -> str:
        mapping = {
            "CLAUDE.md": "First for the full handoff brain",
            "AGENTS.md": "First when the executing agent is Codex",
            "MASTER_PROMPT.md": "Before planning or implementing",
            "PROJECT_BRIEF.md": "At the start for orientation",
            "REQUIREMENTS.md": "Before implementation and before final review",
            "DECISIONS.md": "Before changing scope or resolving ambiguity",
            "NEXT_STEPS.md": "During execution, in order",
            "CONTEXT_INDEX.md": "Before opening converted context files",
            "SOURCE_MAP.md": "Before relying on or citing source material",
            "_logs/raw_input.md": "When raw user intent needs audit",
            "_logs/build_log.md": "When checking preparation history",
            "_logs/readiness_gate.md": "When reviewing build approval or blockers",
        }
        if path in mapping:
            return mapping[path]
        if path.startswith("_context/"):
            return "When using converted material"
        if path.startswith("_sources/"):
            return "Only when original files are required"
        if path.startswith("_skills/"):
            return "When loading specialist execution rules"
        if path.startswith("_versions/"):
            return "When comparing snapshots"
        if path.startswith("_logs/"):
            return "For audit or debugging"
        return "As needed for the current step"

    def _quicklinks(self) -> str:
        links = [
            ("Master prompt goal", "MASTER_PROMPT.md#goal"),
            ("Master prompt requirements", "MASTER_PROMPT.md#requirements"),
            ("Master prompt quality criteria", "MASTER_PROMPT.md#quality-criteria"),
            ("Structured requirements", "REQUIREMENTS.md#specifications"),
            ("Quality criteria", "REQUIREMENTS.md#quality-criteria"),
            ("Decisions and assumptions", "DECISIONS.md#assumptions"),
            ("Next steps", "NEXT_STEPS.md#next-steps"),
            ("Context materials", "CONTEXT_INDEX.md#materials"),
            ("Source provenance", "SOURCE_MAP.md#source-map"),
        ]
        return "\n".join(f"- [{label}]({target})" for label, target in links)

    def _skills_list(self, state: ProjectState | None) -> str:
        if not state or not state.workspace_plan.skills_to_include:
            return "- No specialist skills were included by Amadeus."
        return self._bullet_list(state.workspace_plan.skills_to_include)

    def _decisions_summary(self, state: ProjectState | None) -> str:
        if not state or not state.decisions:
            return (
                "- No project-specific decisions were recorded beyond the default "
                "Amadeus handoff rules."
            )

        rows = []
        for decision in state.decisions:
            approval = "user-approved" if decision.approved_by_user else "not user-approved"
            rationale = f" Rationale: {decision.rationale}" if decision.rationale else ""
            rows.append(f"- {decision.summary} ({approval}).{rationale}")
        return "\n".join(rows)

    def _materials_summary(self, state: ProjectState | None) -> str:
        if not state or not state.materials:
            return "- No source materials were captured. Treat source coverage as limited."

        rows = [
            "| Source ID | Original | Context | Purpose | Status |",
            "|---|---|---|---|---|",
        ]
        for material in state.materials:
            rows.append(
                f"| `{self._table_cell(material.source_id)}` | "
                f"`{self._table_cell(material.original_path)}` | "
                f"`{self._table_cell(material.context_path or '-')}` | "
                f"{self._table_cell(material.purpose or 'Source material')} | "
                f"{self._table_cell(material.status)} |"
            )
        return "\n".join(rows)

    def _next_steps_content(
        self,
        requirements: RequirementsModel,
        state: ProjectState | None,
    ) -> str:
        steps = [
            "Read `CLAUDE.md`, `AGENTS.md`, and `MASTER_PROMPT.md`.",
            "Check `SOURCE_MAP.md` and `CONTEXT_INDEX.md` for source coverage.",
        ]

        if state and any(gap.category == "blocker" for gap in state.gaps):
            steps.append("Resolve or honor the blocker handling recorded in `DECISIONS.md`.")

        for specification in requirements.specifications[:3]:
            steps.append(f"Implement requirement: {specification}")

        if len(requirements.specifications) > 3:
            steps.append("Review remaining requirements in `REQUIREMENTS.md`.")

        steps.extend(
            [
                "Run project-appropriate verification.",
                "Record important scope decisions in `DECISIONS.md`.",
                "Summarize completed work and remaining risks.",
            ]
        )
        return "\n".join(f"{index}. {step}" for index, step in enumerate(steps, 1))

    def _executing_agents(self, state: ProjectState | None) -> list[str]:
        agents = []
        if state:
            agents.extend(state.workspace_plan.executing_agents)
            if state.executing_agent:
                agents.append(state.executing_agent)

        if not agents:
            agents = ["Codex", "Claude Code", "Antigravity"]

        deduped = []
        for agent in agents:
            if agent and agent not in deduped:
                deduped.append(agent)
        return deduped

    def _prompt_version(self, state: ProjectState | None) -> str:
        if not state or not state.prompt_versions:
            return "`MASTER_PROMPT.md` (version not recorded)"

        latest = state.prompt_versions[-1]
        return f"v{latest.version} at `{latest.path}` ({latest.created_at})"

    def _table_cell(self, value: str) -> str:
        return str(value).replace("\n", " ").replace("|", "\\|")

    def _project_brief(
        self,
        requirements: RequirementsModel,
        generated_at: str,
        state: ProjectState | None,
    ) -> str:
        readiness = (
            f"Readiness score: {state.readiness.score}/100\nState phase: {state.phase.value}\n"
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
        sections = ["# Context Index\n", "## Materials"]
        mat_rows = [
            "| # | Context File | Type | Purpose | Extraction Notes |",
            "|---|---|---|---|---|",
        ]

        has_materials = False
        if state:
            for i, material in enumerate(state.materials, 1):
                has_materials = True
                notes = "; ".join(material.extraction_notes) or material.status
                mat_rows.append(
                    f"| {i} | `{material.context_path}` | {material.material_type} | "
                    f"{material.purpose or 'Source material'} | {notes} |"
                )

        if not has_materials:
            mat_rows.append("| - | - | - | - | - |")

        sections.append("\n".join(mat_rows) + "\n")

        sections.append("## Links")
        link_rows = ["| # | URL | Purpose | Status |", "|---|---|---|---|"]

        has_links = False
        if state:
            for i, link in enumerate(state.links, 1):
                has_links = True
                link_rows.append(f"| {i} | `{link.url}` | {link.purpose} | {link.status} |")

        if not has_links:
            link_rows.append("| - | - | - | - |")

        sections.append("\n".join(link_rows) + "\n")

        return "\n".join(sections)

    def _source_map(self, state: ProjectState | None) -> str:
        rows = [
            "| Source ID | Original | Converted | Purpose | Status |",
            "|---|---|---|---|---|",
        ]

        has_sources = False
        if state:
            for material in state.materials:
                has_sources = True
                rows.append(
                    f"| {material.source_id} | `{material.original_path}` | "
                    f"`{material.context_path or ''}` | "
                    f"{material.purpose or 'Source material'} | {material.status} |"
                )

        if not has_sources:
            rows.append("| - | - | - | - | - |")

        return "# Source Map\n\n" + "\n".join(rows) + "\n"

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

    def _build_log(self, state: ProjectState | None, readiness_report: str, timestamp: str) -> str:
        log = [
            f"# Build Log\n\nBuilt at: {timestamp}\n",
            "## Phases\n",
            f"- Current Phase: {state.phase.value if state else 'unknown'}\n",
        ]

        if state:
            log.append("\n## Materials Processed\n")
            if state.materials:
                for mat in state.materials:
                    log.append(f"- {mat.source_id}: {mat.status} ({mat.original_path})")
            else:
                log.append("- No materials processed.")

            log.append("\n## Gap Analysis Summary\n")
            blocker_count = len([g for g in state.gaps if g.category == "blocker"])
            assumption_count = len([g for g in state.gaps if g.category == "assumption"])
            optional_count = len([g for g in state.gaps if g.category == "optional"])
            log.append(f"- Blockers: {blocker_count}")
            log.append(f"- Assumptions: {assumption_count}")
            log.append(f"- Optional: {optional_count}")

        log.append("\n## Readiness Result\n")
        if readiness_report:
            if "Build status: Blocked" in readiness_report:
                log.append("Result: Blocked")
            else:
                log.append("Result: Passed / Approved")
        else:
            log.append("Result: Unknown")

        return "\n".join(log) + "\n"

    def _skills_readme(self, state: ProjectState | None) -> str:
        base = "# Skills\n\nOptional specialist execution instructions belong here.\n"
        if not state or not state.workspace_plan.skills_to_include:
            return base

        skills = "\n".join(f"- {skill}" for skill in state.workspace_plan.skills_to_include)
        return f"{base}\n## Included Skills\n\n{skills}\n"

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

        return "\n".join(f"- {gap.title} ({gap.status}): {gap.detail}" for gap in gaps)

    def _file_table(self, requirements: RequirementsModel) -> str:
        rows = ["| File | Purpose |", "|---|---|"]
        for file in requirements.files_to_create:
            path = os.path.normpath(file.file_path).replace("\\", "/")
            rows.append(f"| `{path}` | {file.purpose} |")
        return "\n".join(rows)
