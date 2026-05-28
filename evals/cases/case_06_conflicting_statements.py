from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_06",
    title="Conflicting user statements",
    description="Input contains conflicting project goals.",
    category="contradiction",
    input=EvalCaseInput(
        raw_text="Build a REST API. Actually no, build a CLI tool. The output should be a web app.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_assumption_keywords=[],
    ),
)
