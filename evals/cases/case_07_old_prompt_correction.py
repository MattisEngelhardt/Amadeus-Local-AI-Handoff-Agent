from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_07",
    title="Old prompt with correction",
    description="Correcting an old instruction.",
    category="contradiction",
    input=EvalCaseInput(
        raw_text="I previously said build a Django app. Forget that. Build a FastAPI service instead.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_blocker_keywords=[],
    ),
)
