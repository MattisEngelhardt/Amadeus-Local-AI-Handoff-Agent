from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_10",
    title="Claude Code + Codex handoff",
    description="Handoff to both Claude Code and Codex.",
    category="handoff_target",
    input=EvalCaseInput(
        raw_text="Build a Python data pipeline. Hand off to Claude Code and Codex.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_generated_files=[
            "CLAUDE.md",
            "AGENTS.md",
            "MASTER_PROMPT.md",
            "PROJECT_BRIEF.md",
            "REQUIREMENTS.md",
            "DECISIONS.md",
            "NEXT_STEPS.md",
            "CONTEXT_INDEX.md",
            "SOURCE_MAP.md",
        ],
    ),
)
