from unittest.mock import MagicMock, patch
from speech_to_code.core.analyzer import TranscriptAnalyzer
from speech_to_code.models.requirements import RequirementsModel

@patch('speech_to_code.core.analyzer.Anthropic')
def test_transcript_analysis(mock_anthropic):
    # 1. Arrange mock client and Claude response structure
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # Create mock tool use block
    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.name = "save_requirements"
    mock_tool_use.input = {
        "project_name": "test-tracker",
        "display_name": "Test Tracker",
        "short_description": "A mock application to track testing files.",
        "project_type": "Python CLI Tool",
        "tech_stack": ["Python", "SQLite"],
        "dependencies": ["pytest", "pyyaml"],
        "specifications": [
            "User should be able to run tests easily",
            "Store log history in SQLite"
        ],
        "quality_criteria": [
            "Follow PEP 8 styling conventions"
        ],
        "files_to_create": [
            {"file_path": "main.py", "purpose": "Runs the main application process"},
            {"file_path": "db.py", "purpose": "Handles SQLite database connections"}
        ]
    }
    
    # Pack the mock block into client response message
    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]
    mock_client.messages.create.return_value = mock_response
    
    # 2. Act
    analyzer = TranscriptAnalyzer(api_key="dummy_api_key_value")
    result = analyzer.analyze("I want a test tracker in python that logs tests in sqlite.")
    
    # 3. Assert
    assert result is not None
    assert isinstance(result, RequirementsModel)
    assert result.project_name == "test-tracker"
    assert result.display_name == "Test Tracker"
    assert "SQLite" in result.tech_stack
    assert len(result.files_to_create) == 2
    assert result.files_to_create[0].file_path == "main.py"
    assert result.files_to_create[1].file_path == "db.py"
    
    # Verify Claude API was called with the correct parameters
    mock_client.messages.create.assert_called_once()


@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_transcript_analysis_gemini(mock_configure, mock_model_class):
    # Arrange mock model and response
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    
    mock_response = MagicMock()
    mock_response.text = """{
      "project_name": "test-tracker",
      "display_name": "Test Tracker",
      "short_description": "A mock application to track testing files.",
      "project_type": "Python CLI Tool",
      "tech_stack": ["Python", "SQLite"],
      "dependencies": ["pytest", "pyyaml"],
      "specifications": [
        "User should be able to run tests easily",
        "Store log history in SQLite"
      ],
      "quality_criteria": [
        "Follow PEP 8 styling conventions"
      ],
      "files_to_create": [
        {"file_path": "main.py", "purpose": "Runs the main application process"},
        {"file_path": "db.py", "purpose": "Handles SQLite database connections"}
      ]
    }"""
    mock_model.generate_content.return_value = mock_response
    
    # Act
    analyzer = TranscriptAnalyzer(api_key="dummy_gemini_key", llm_provider="gemini")
    result = analyzer.analyze("I want a test tracker in python that logs tests in sqlite.")
    
    # Assert
    assert result is not None
    assert isinstance(result, RequirementsModel)
    assert result.project_name == "test-tracker"
    assert result.display_name == "Test Tracker"
    assert "SQLite" in result.tech_stack
    assert len(result.files_to_create) == 2
    
    mock_configure.assert_called()
    mock_model.generate_content.assert_called_once()
