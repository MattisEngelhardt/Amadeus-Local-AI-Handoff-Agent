from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_04",
    title="Text material ingestion",
    description="Build from a text material file.",
    category="material",
    input=EvalCaseInput(
        raw_text="Build the system based on the attached design notes.",
        source_files=["fixtures/design_notes.txt"],
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_material_count=1,
        expected_material_statuses=["converted"],
        source_map_must_contain=["design_notes.txt"],
    ),
)
