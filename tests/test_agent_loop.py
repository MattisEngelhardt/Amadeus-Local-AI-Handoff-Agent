from unittest.mock import MagicMock

import pytest
from amadeus.core.agent_loop import AgentLoop
from amadeus.models.state import ProjectState
from amadeus.models.tools import AgentDecision, ToolAction


@pytest.fixture
def empty_state():
    return ProjectState(project_name="test", display_name="Test", main_goal="Goal")


@pytest.fixture
def mock_client():
    client = MagicMock()
    return client


def test_agent_loop_dry_run(empty_state, mock_client, tmp_path):
    loop = AgentLoop(empty_state, tmp_path, mock_client, dry_run=True)
    loop.MAX_STEPS = 1

    decision = AgentDecision(
        observation="Testing",
        reasoning="Because",
        action=ToolAction(tool="create_project", reason="", parameters={"raw_text": "hello"}),
        done=True,
    )
    mock_client.generate_structured.return_value = decision

    state = loop.run()
    assert len(loop.action_log) == 1
    assert loop.action_log[0].result.output == "[dry-run] Not executed."


def test_agent_loop_stops_at_max_steps(empty_state, mock_client, tmp_path):
    loop = AgentLoop(empty_state, tmp_path, mock_client, dry_run=True)
    loop.MAX_STEPS = 3

    decision = AgentDecision(
        observation="Testing",
        reasoning="Because",
        action=ToolAction(tool="create_project", reason="", parameters={"raw_text": "hello"}),
        done=False,
    )
    mock_client.generate_structured.return_value = decision

    loop.run()
    assert len(loop.action_log) == 3


def test_agent_loop_rejects_tool_not_in_mode(empty_state, mock_client, tmp_path):
    loop = AgentLoop(empty_state, tmp_path, mock_client, dry_run=True)
    loop.MAX_STEPS = 1

    # In intake mode, build_workspace is not allowed
    decision = AgentDecision(
        observation="Testing",
        reasoning="Because",
        action=ToolAction(tool="build_workspace", reason="", parameters={}),
        done=False,
    )
    mock_client.generate_structured.return_value = decision

    loop.run()
    assert loop.action_log[0].result.success is False
    assert "Tool not allowed" in loop.action_log[0].result.error
