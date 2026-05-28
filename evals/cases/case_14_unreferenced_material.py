from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_14",
    title="Unreferenced material",
    description="Material provided but not referenced in text.",
    category="material",
    input=EvalCaseInput(
        raw_text="Build a simple Python calculator application that supports basic arithmetic operations like addition, subtraction, multiplication, and division.",
        source_files=["fixtures/random_notes.txt"],
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_material_count=1,
        expected_material_statuses=["converted"],
    ),
)
