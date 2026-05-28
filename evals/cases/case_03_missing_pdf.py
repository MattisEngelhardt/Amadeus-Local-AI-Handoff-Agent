from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_03",
    title="Missing PDF reference",
    description="Input references an attached PDF but none is provided.",
    category="missing_context",
    input=EvalCaseInput(
        raw_text="Build a report from the attached PDF file and preserve citations.",
    ),
    expectation=EvalCaseExpectation(
        should_build=False,
        should_block=True,
        expected_blocker_keywords=["materials", "missing"],
    ),
)
