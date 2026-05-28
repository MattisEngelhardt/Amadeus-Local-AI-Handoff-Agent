
import pytest
from amadeus.core.tool_executor import ToolExecutor
from amadeus.models.state import GapItem, ProjectState
from amadeus.models.tools import ToolAction


@pytest.fixture
def empty_state():
    return ProjectState(project_name="test", display_name="Test", main_goal="Goal")


def test_execute_create_project(empty_state, tmp_path):
    executor = ToolExecutor(empty_state, tmp_path)
    action = ToolAction(
        tool="create_project", reason="Testing", parameters={"raw_text": "Build a test app"}
    )

    # We mock validator to not invoke Ollama in tests
    from unittest.mock import patch

    from amadeus.models.requirements import RequirementsModel

    reqs = RequirementsModel(
        project_name="new-app",
        display_name="New App",
        short_description="Desc",
        project_type="Test",
        tech_stack=[],
        dependencies=[],
        specifications=[],
        quality_criteria=[],
        files_to_create=[],
    )

    with patch("amadeus.core.validator.RequirementsValidator.validate", return_value=reqs):
        result = executor.execute(action)

    assert result.success is True
    assert executor.state.project_name == "new-app"


def test_execute_ingest_material(empty_state, tmp_path):
    executor = ToolExecutor(empty_state, tmp_path)
    fixture_file = tmp_path / "test.txt"
    fixture_file.write_text("Hello", encoding="utf-8")

    action = ToolAction(
        tool="ingest_material", reason="Test", parameters={"source_path": str(fixture_file)}
    )
    result = executor.execute(action)

    assert result.success is True
    assert len(executor.state.materials) == 1


def test_execute_run_gap_analysis(empty_state, tmp_path):
    executor = ToolExecutor(empty_state, tmp_path)
    action = ToolAction(tool="run_gap_analysis", reason="Test", parameters={})

    result = executor.execute(action)
    assert result.success is True
    assert "complete" in result.output


def test_execute_build_workspace_with_blocker_blocked(empty_state, tmp_path):
    empty_state.gaps.append(GapItem(gap_id="g1", category="blocker", title="B1", detail="D1"))
    executor = ToolExecutor(empty_state, tmp_path)

    action = ToolAction(tool="build_workspace", reason="Test", parameters={})
    result = executor.execute(action)
    assert result.success is False
    assert "open blockers exist" in result.error


def test_execute_unknown_tool_fails(empty_state, tmp_path):
    executor = ToolExecutor(empty_state, tmp_path)
    # Pydantic validates literal, but let's bypass
    action = ToolAction.model_construct(tool="non_existent", reason="", parameters={})
    result = executor.execute(action)
    assert result.success is False
    assert "Unknown tool" in result.error


def test_execute_missing_required_param_fails(empty_state, tmp_path):
    executor = ToolExecutor(empty_state, tmp_path)
    action = ToolAction(tool="create_project", reason="", parameters={})
    result = executor.execute(action)
    assert result.success is False
    assert "Missing required param" in result.error
