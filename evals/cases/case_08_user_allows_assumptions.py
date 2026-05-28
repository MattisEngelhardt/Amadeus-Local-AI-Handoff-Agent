from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_08",
    title="User explicitly allows assumptions",
    description="User provides approval to proceed despite missing PDF.",
    category="missing_context",
    input=EvalCaseInput(
        raw_text="Build a report from the attached PDF. Proceed with assumptions.",
        approve_readiness=True,
        approval_note="PDF will follow later.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        should_block=False,
    ),
)
