from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_13",
    title="Markdown material",
    description="Build from a markdown file.",
    category="material",
    input=EvalCaseInput(
        raw_text="Build the project described in the attached specification.",
        source_files=["fixtures/project_spec.md"],
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_material_count=1,
        expected_material_statuses=["converted"],
    ),
)
