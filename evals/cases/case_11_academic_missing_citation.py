from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_11",
    title="Academic project with missing citation style",
    description="Mentions sources but provides none.",
    category="academic",
    input=EvalCaseInput(
        raw_text="Schreibe eine Hausarbeit über maschinelles Lernen. Nutze wissenschaftliche Quellen.",
    ),
    expectation=EvalCaseExpectation(
        should_build=False,
        should_block=True,
        expected_blocker_keywords=["materials", "sources"],
    ),
)
