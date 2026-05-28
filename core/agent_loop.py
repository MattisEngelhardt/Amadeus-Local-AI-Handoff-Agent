import logging
from pathlib import Path

from amadeus.core.modes import MODES, AgentMode
from amadeus.core.ollama_client import OllamaClient
from amadeus.core.tool_executor import ToolExecutor
from amadeus.models.state import ProjectState
from amadeus.models.tools import ActionRecord, AgentDecision, ToolResult

logger = logging.getLogger(__name__)


class AgentLoop:
    MAX_STEPS = 20

    def __init__(
        self,
        state: ProjectState,
        project_path: Path,
        client: OllamaClient,
        model: str = "amadeus",
        dry_run: bool = False,
    ):
        self.state = state
        self.project_path = project_path
        self.executor = ToolExecutor(state, project_path)
        self.client = client
        self.model = model
        self.dry_run = dry_run
        self.action_log: list[ActionRecord] = []
        self.current_mode: str = "intake"

    def run(self, initial_text: str = "") -> ProjectState:
        for step in range(self.MAX_STEPS):
            mode = MODES[self.current_mode]

            context = self._build_context(mode, initial_text)
            decision = self._ask_gemma(context, mode)

            if decision.action.tool not in mode.allowed_tools:
                logger.warning(f"Tool {decision.action.tool} not allowed in mode {mode.name}")
                result = ToolResult(
                    tool=decision.action.tool,
                    success=False,
                    error="Tool not allowed in current mode.",
                )
            else:
                if self.dry_run:
                    result = ToolResult(
                        tool=decision.action.tool, success=True, output="[dry-run] Not executed."
                    )
                else:
                    result = self.executor.execute(decision.action)

            record = ActionRecord(step=step, decision=decision, result=result)
            self.action_log.append(record)

            # Sync back executor state changes to loop tracking
            self.state = self.executor.state

            if decision.done:
                next_mode = self._next_mode()
                if next_mode is None:
                    break
                self.current_mode = next_mode

        # Ensure action log is saved to state
        if hasattr(self.state, "action_log"):
            self.state.action_log.extend(self.action_log)

        return self.state

    def _ask_gemma(self, context: str, mode: AgentMode) -> AgentDecision:
        return self.client.generate_structured(
            prompt=context,
            model=self.model,
            system=mode.system_prompt,
            response_model=AgentDecision,
            options={"temperature": 0.2},
        )

    def _build_context(self, mode: AgentMode, initial_text: str) -> str:
        # Include current state summary, previous actions, available tools
        ctx = [f"Initial Text: {initial_text}"]
        ctx.append(f"Current State: {self.state.phase.value}")
        ctx.append(f"Materials: {len(self.state.materials)}")
        ctx.append(f"Open Blockers: {len(self.state.open_blockers())}")
        if self.action_log:
            last = self.action_log[-1]
            ctx.append(
                f"Last Action Result: {last.result.success} - {last.result.output} {last.result.error}"
            )
        return "\n".join(ctx)

    def _next_mode(self) -> str | None:
        order = [
            "intake",
            "gap_analyst",
            "prompt_compiler",
            "workspace_architect",
            "build_orchestrator",
        ]
        if self.current_mode in order:
            idx = order.index(self.current_mode)
            if idx + 1 < len(order):
                return order[idx + 1]
        return None
