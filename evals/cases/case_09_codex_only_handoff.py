from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_09",
    title="Codex-only handoff",
    description="Build exclusively for Codex.",
    category="handoff_target",
    input=EvalCaseInput(
        raw_text="Build a Node.js CLI tool. This workspace is exclusively for Codex.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_generated_files=[
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
