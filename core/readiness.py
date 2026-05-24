from __future__ import annotations

import hashlib

from amadeus.models.state import DecisionRecord, ProjectState


class ReadinessGate:
    """Renders and enforces the Amadeus pre-build readiness gate."""

    def can_build(self, state: ProjectState) -> bool:
        return not state.open_blockers()

    def approve(self, state: ProjectState, note: str) -> ProjectState:
        for gap in state.open_blockers():
            gap.status = "waived"

        state.readiness_approved = True
        state.approval_note = note
        state.decisions.append(
            DecisionRecord(
                decision_id=self._stable_id("approval", state.project_name, note),
                summary="Readiness gate approved with documented gaps",
                rationale=note,
                approved_by_user=True,
            )
        )
        state.readiness.can_build = True
        state.readiness.approval_required = False
        state.readiness.open_blockers = []
        state.touch()
        return state

    def render_markdown(self, state: ProjectState) -> str:
        build_status = "Allowed" if self.can_build(state) else "Blocked"
        blockers = self._gap_lines(state, "blocker")
        assumptions = self._gap_lines(state, "assumption")
        optional_items = self._gap_lines(state, "optional")
        materials = self._materials_lines(state)
        missing_materials = self._list_lines(state.readiness.missing_materials)
        planned_directories = self._list_lines(state.workspace_plan.planned_directories)
        planned_files = self._list_lines(state.workspace_plan.planned_files)
        questions = self._list_lines(state.open_questions)

        return f"""# Readiness Gate

Build status: {build_status}
Readiness score: {state.readiness.score}/100
Phase: {state.phase.value}

## Project

- Name: {state.display_name}
- Target path: `{state.target_path or state.workspace_plan.target_path}`
- Main goal: {state.main_goal}
- Planned executing agent: {state.executing_agent}

## Received Materials

{materials}

## Missing Materials

{missing_materials}

## Open Blockers

{blockers}

## Recorded Assumptions

{assumptions}

## Optional Improvements

{optional_items}

## Targeted Questions

{questions}

## Planned File Tree

Directories:

{planned_directories}

Files:

{planned_files}

## Decision

{self._decision_text(state)}
"""

    def _decision_text(self, state: ProjectState) -> str:
        if self.can_build(state):
            if state.readiness_approved:
                return f"Build approved by user with note: {state.approval_note}"
            return "Build may proceed because no open blockers remain."
        return "Build must not proceed until blockers are resolved or explicitly waived."

    def _gap_lines(self, state: ProjectState, category: str) -> str:
        items = [gap for gap in state.gaps if gap.category == category]
        if not items:
            return "- None."
        return "\n".join(
            f"- {gap.title} ({gap.status}): {gap.detail}" for gap in items
        )

    def _materials_lines(self, state: ProjectState) -> str:
        if not state.materials:
            return "- None registered."
        return "\n".join(
            f"- {item.source_id}: `{item.original_path}` -> "
            f"`{item.context_path or 'not converted'}`"
            for item in state.materials
        )

    def _list_lines(self, items: list[str]) -> str:
        if not items:
            return "- None."
        return "\n".join(f"- {item}" for item in items)

    def _stable_id(self, *parts: str) -> str:
        digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
        return f"decision-{digest}"
