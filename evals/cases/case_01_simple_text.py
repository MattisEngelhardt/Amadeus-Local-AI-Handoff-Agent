from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_01",
    title="Simple text-only project",
    description="Build a simple Python REST API with SQLite.",
    category="text_only",
    input=EvalCaseInput(
        raw_text="Build a Python REST API that serves weather data from a local SQLite database.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        min_readiness_score=70,
        expected_blocker_keywords=[],
    ),
)
