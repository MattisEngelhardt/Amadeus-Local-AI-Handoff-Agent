from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput

CASE = EvalCase(
    case_id="case_05",
    title="Multiple materials",
    description="Build from multiple material files.",
    category="material",
    input=EvalCaseInput(
        raw_text="Use the attached specification and the architecture notes to build the workspace.",
        source_files=["fixtures/spec.md", "fixtures/arch_notes.txt"],
    ),
    expectation=EvalCaseExpectation(
        should_build=True,
        expected_material_count=2,
        expected_material_statuses=["converted", "converted"],
        source_map_must_contain=["spec.md", "arch_notes.txt"],
    ),
)
