from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_12",
    title="Telegram-style multi-message transcript",
    description="Multi-line simulated Telegram messages.",
    category="text_only",
    input=EvalCaseInput(
        raw_text="Build a task manager.\nAdd SQLite storage.\nMake it a CLI.\nUse Click for the CLI.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
    ),
)
