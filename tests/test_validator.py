from amadeus.core.validator import CANONICAL_HANDOFF_FILES, RequirementsValidator
from amadeus.models.requirements import RequirementsModel


def test_requirements_validation_enforces_handoff_contract():
    initial_reqs = RequirementsModel(
        project_name="Test Project!!",
        display_name="Test Project",
        short_description="Prepare a handoff workspace.",
        project_type="Python CLI Tool",
        tech_stack=["Python"],
        dependencies=["openai", "anthropic"],
        specifications=[],
        quality_criteria=[],
        files_to_create=[],
    )

    result = RequirementsValidator().validate(
        original_transcript="Raw user input",
        requirements=initial_reqs,
    )

    assert result.project_name == "test-project"
    assert result.project_type == "AI handoff workspace"
    assert result.dependencies == []
    generated_paths = {file.file_path for file in result.files_to_create}
    for file_path, _purpose in CANONICAL_HANDOFF_FILES:
        assert file_path in generated_paths
    assert any("raw input" in item.lower() for item in result.specifications)
    assert any("do not invent" in item.lower() for item in result.quality_criteria)
