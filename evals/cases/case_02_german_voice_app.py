from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_02",
    title="German voice-style app idea",
    description="German input, English workspace expected.",
    category="voice",
    input=EvalCaseInput(
        raw_text="Ich brauch eine App die meine Studiennotizen zusammenfasst und daraus Karteikarten macht. Am besten mit Python und einer einfachen Web-Oberfläche.",
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_blocker_keywords=[],
    ),
)
