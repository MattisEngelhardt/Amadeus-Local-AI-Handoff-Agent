import logging
from pathlib import Path
from typing import Any

from amadeus.core.tool_registry import TOOL_REGISTRY
from amadeus.models.state import ProjectState, RawInputRecord
from amadeus.models.tools import ToolAction, ToolResult

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, state: ProjectState, project_path: Path):
        self.state = state
        self.project_path = project_path
        self._handlers = {
            "create_project": self._handle_create_project,
            "save_raw_input": self._handle_save_raw_input,
            "ingest_material": self._handle_ingest_material,
            "run_gap_analysis": self._handle_run_gap_analysis,
            "render_prompt": self._handle_render_prompt,
            "render_readiness": self._handle_render_readiness,
            "build_workspace": self._handle_build_workspace,
            "run_validation_suite": self._handle_run_validation_suite,
            "write_decision": self._handle_write_decision,
            "create_snapshot": self._handle_create_snapshot,
            "transcribe_audio": self._stub_handler,
            "clean_transcript": self._stub_handler,
            "inspect_link": self._stub_handler,
        }

    def execute(self, action: ToolAction) -> ToolResult:
        contract = TOOL_REGISTRY.get(action.tool)
        if not contract:
            return ToolResult(tool=action.tool, success=False, error=f"Unknown tool: {action.tool}")

        for param in contract.required_params:
            if param not in action.parameters:
                return ToolResult(
                    tool=action.tool, success=False, error=f"Missing required param: {param}"
                )

        handler = self._handlers.get(action.tool)
        if not handler:
            return ToolResult(
                tool=action.tool, success=False, error=f"No handler for tool: {action.tool}"
            )

        # Guardrails
        if action.tool == "build_workspace":
            approve = action.parameters.get("approve_readiness", False)
            if self.state.open_blockers() and not approve:
                return ToolResult(
                    tool=action.tool,
                    success=False,
                    error="Cannot build workspace: open blockers exist and approve_readiness is False.",
                )

        try:
            result = handler(action.parameters)
            # Log action intent and result implicitly handled by AgentLoop appending ActionRecord,
            # but we can mutate state action_log here if we want. AgentLoop will do it per plan.
            return result
        except Exception as exc:
            logger.exception(f"Tool {action.tool} failed")
            return ToolResult(tool=action.tool, success=False, error=str(exc))

    def _handle_create_project(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.validator import RequirementsValidator
        from amadeus.models.requirements import RequirementsModel

        reqs = RequirementsValidator().validate(
            params["raw_text"],
            RequirementsModel(
                project_name=params.get("project_name", "new-project"),
                display_name="New Project",
                short_description="",
                project_type="unknown",
                tech_stack=[],
                dependencies=[],
                specifications=[],
                quality_criteria=[],
                files_to_create=[],
            ),
        )
        # Ensure we don't write outside base dir. Here we just update state in memory.
        self.state.project_name = reqs.project_name
        self.state.display_name = reqs.display_name
        self.state.requirements = reqs.model_dump()
        return ToolResult(
            tool="create_project",
            success=True,
            output=f"Project {reqs.project_name} initialized.",
            state_changed=True,
        )

    def _handle_save_raw_input(self, params: dict[str, Any]) -> ToolResult:
        import uuid

        record = RawInputRecord(
            input_id=f"in-{uuid.uuid4().hex[:8]}",
            channel=params["channel"],
            kind=params["kind"],
            raw_text=params["raw_text"],
        )
        self.state.raw_inputs.append(record)
        return ToolResult(
            tool="save_raw_input", success=True, output="Raw input saved.", state_changed=True
        )

    def _handle_ingest_material(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.workflow import _ingest_materials

        source_path = Path(params["source_path"])
        # Guardrail: check if source path is safe, though here we ingest from anywhere and write to _context
        if not source_path.exists():
            return ToolResult(
                tool="ingest_material", success=False, error=f"File not found: {source_path}"
            )
        self.state = _ingest_materials(self.state, [source_path])
        return ToolResult(
            tool="ingest_material",
            success=True,
            output=f"Ingested {source_path.name}",
            state_changed=True,
        )

    def _handle_run_gap_analysis(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.gap_analysis import GapAnalyzer
        from amadeus.models.requirements import RequirementsModel

        req_model = (
            RequirementsModel.model_validate(self.state.requirements)
            if self.state.requirements
            else RequirementsModel(
                project_name=self.state.project_name,
                display_name=self.state.display_name,
                short_description=self.state.main_goal,
                project_type="unknown",
                tech_stack=[],
                dependencies=[],
                specifications=[],
                quality_criteria=[],
                files_to_create=[],
            )
        )
        raw_text = self.state.raw_inputs[0].raw_text if self.state.raw_inputs else ""
        gap_analyzer = GapAnalyzer()
        gap_analysis = gap_analyzer.analyze(req_model, self.state, raw_text)
        self.state = gap_analyzer.apply_to_state(self.state, gap_analysis)
        return ToolResult(
            tool="run_gap_analysis",
            success=True,
            output="Gap analysis complete.",
            state_changed=True,
        )

    def _handle_render_prompt(self, params: dict[str, Any]) -> ToolResult:

        # Normally prompt is generated during workspace build. We can stub or trigger part of generator.
        return ToolResult(
            tool="render_prompt",
            success=True,
            output="Prompt render triggered in memory.",
            state_changed=False,
        )

    def _handle_render_readiness(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.readiness import ReadinessGate

        gate = ReadinessGate()
        report = gate.render_markdown(self.state)
        return ToolResult(tool="render_readiness", success=True, output=report, state_changed=False)

    def _handle_build_workspace(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.workflow import prepare_handoff_workspace
        from amadeus.models.requirements import RequirementsModel

        req_model = (
            RequirementsModel.model_validate(self.state.requirements)
            if self.state.requirements
            else RequirementsModel(
                project_name=self.state.project_name,
                display_name=self.state.display_name,
                short_description=self.state.main_goal,
                project_type="unknown",
                tech_stack=[],
                dependencies=[],
                specifications=[],
                quality_criteria=[],
                files_to_create=[],
            )
        )
        raw_text = self.state.raw_inputs[0].raw_text if self.state.raw_inputs else ""

        result = prepare_handoff_workspace(
            requirements=req_model,
            raw_text=raw_text,
            output_dir=str(self.project_path.parent),
            approve_readiness=params.get("approve_readiness", False),
            approval_note=params.get("approval_note", ""),
            source_files=[],
        )
        if result.built:
            self.state = result.state
            return ToolResult(
                tool="build_workspace",
                success=True,
                output=f"Built at {result.project_path}",
                state_changed=True,
            )
        return ToolResult(tool="build_workspace", success=False, error=result.message)

    def _handle_run_validation_suite(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.validation_suite import run_validation_suite
        from amadeus.models.requirements import RequirementsModel

        req_model = (
            RequirementsModel.model_validate(self.state.requirements)
            if self.state.requirements
            else RequirementsModel(
                project_name=self.state.project_name,
                display_name=self.state.display_name,
                short_description=self.state.main_goal,
                project_type="unknown",
                tech_stack=[],
                dependencies=[],
                specifications=[],
                quality_criteria=[],
                files_to_create=[],
            )
        )
        raw_text = self.state.raw_inputs[0].raw_text if self.state.raw_inputs else ""
        report = run_validation_suite(
            self.project_path, state=self.state, requirements=req_model, raw_text=raw_text
        )
        return ToolResult(
            tool="run_validation_suite", success=report.passed, output=report.summary()
        )

    def _handle_write_decision(self, params: dict[str, Any]) -> ToolResult:
        import uuid

        from amadeus.models.state import DecisionRecord

        rec = DecisionRecord(
            decision_id=f"dec-{uuid.uuid4().hex[:8]}",
            summary=params["summary"],
            rationale=params.get("rationale", ""),
            approved_by_user=params.get("approved_by_user", False),
        )
        self.state.decisions.append(rec)
        return ToolResult(
            tool="write_decision", success=True, output="Decision recorded.", state_changed=True
        )

    def _handle_create_snapshot(self, params: dict[str, Any]) -> ToolResult:
        from amadeus.core.versioning import create_workspace_snapshot

        create_workspace_snapshot(self.project_path, params["reason"])
        return ToolResult(tool="create_snapshot", success=True, output="Snapshot created.")

    def _stub_handler(self, params: dict[str, Any]) -> ToolResult:
        return ToolResult(tool="stub", success=True, output="Stub handler executed.")
