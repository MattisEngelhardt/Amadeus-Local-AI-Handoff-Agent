from unittest.mock import MagicMock, patch
from speech_to_code.core.validator import RequirementsValidator
from speech_to_code.models.requirements import RequirementsModel, FilePlaceholder

@patch('speech_to_code.core.validator.Anthropic')
def test_requirements_validation(mock_anthropic):
    # 1. Arrange mock client and Claude response structure
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # Create mock tool use block representing a corrected requirements output
    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.name = "save_requirements"
    mock_tool_use.input = {
        "project_name": "test-project-corrected",
        "display_name": "Test Project Corrected",
        "short_description": "Corrected description of the application.",
        "project_type": "Python CLI Tool",
        "tech_stack": ["Python"],
        "dependencies": ["pytest"],
        "specifications": ["Core specification is now corrected"],
        "quality_criteria": ["Clean structure"],
        "files_to_create": [
            {"file_path": "main.py", "purpose": "Corrected entrypoint purpose"}
        ]
    }
    
    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]
    mock_client.messages.create.return_value = mock_response
    
    initial_reqs = RequirementsModel(
        project_name="test-project",
        display_name="Test Project",
        short_description="Initial description.",
        project_type="Python CLI Tool",
        tech_stack=["Python"],
        dependencies=["pytest"],
        specifications=["Original specification"],
        quality_criteria=["Clean structure"],
        files_to_create=[
            FilePlaceholder(file_path="main.py", purpose="Original entrypoint purpose")
        ]
    )

    # 2. Act
    validator = RequirementsValidator(api_key="dummy_api_key_value")
    result = validator.validate(
        original_transcript="My transcript text...",
        requirements=initial_reqs,
        max_iterations=1
    )

    # 3. Assert
    assert result is not None
    assert isinstance(result, RequirementsModel)
    assert result.project_name == "test-project-corrected"
    assert result.display_name == "Test Project Corrected"
    assert result.short_description == "Corrected description of the application."
    assert result.specifications[0] == "Core specification is now corrected"
    assert result.files_to_create[0].purpose == "Corrected entrypoint purpose"
    
    # Verify Claude API was called
    mock_client.messages.create.assert_called_once()
