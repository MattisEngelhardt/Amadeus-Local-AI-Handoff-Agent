from pathlib import Path
from unittest.mock import patch

import pytest
from amadeus.__main__ import main
from amadeus.core.project_registry import ProjectRegistry


@pytest.fixture
def mock_registry(tmp_path):
    registry_file = tmp_path / "projects.json"
    registry = ProjectRegistry(registry_file=registry_file)
    with patch("amadeus.core.cli.ProjectRegistry", return_value=registry):
        yield registry


def test_new_command_creates_project(mock_registry, tmp_path, monkeypatch):
    # Mock analyzer to avoid Ollama calls
    from amadeus.models.requirements import RequirementsModel

    reqs = RequirementsModel(
        project_name="test-new",
        display_name="Test New",
        short_description="desc",
        project_type="test",
        tech_stack=[],
        dependencies=[],
        specifications=["Build a test project"],
        quality_criteria=[],
        files_to_create=[],
    )
    with patch("amadeus.core.cli.TranscriptAnalyzer.analyze", return_value=reqs):
        result = main(["new", "Build a test project", "--output-dir", str(tmp_path)])
        assert result == 0
        active = mock_registry.get_active()
        assert active is not None
        assert active.project_name == "test-new"
        assert Path(active.project_path).exists()


def test_add_command_ingests_material(mock_registry, tmp_path):
    from amadeus.core.state_store import ProjectStateStore
    from amadeus.models.state import ProjectRegistryEntry, ProjectState

    project_dir = tmp_path / "test-add"
    project_dir.mkdir()

    state = ProjectState(project_name="test-add", display_name="Test Add", main_goal="Goal")
    store = ProjectStateStore()
    store.save(state, project_dir)

    mock_registry.register(
        ProjectRegistryEntry(
            project_name="test-add",
            display_name="Test Add",
            project_path=str(project_dir),
            is_active=True,
        )
    )

    fixture_file = tmp_path / "fixture.txt"
    fixture_file.write_text("Material content", encoding="utf-8")

    result = main(["add", str(fixture_file)])
    assert result == 0

    updated_state = store.load(project_dir)
    assert len(updated_state.materials) == 1


def test_status_command_prints_summary(mock_registry, tmp_path, capsys):
    from amadeus.core.state_store import ProjectStateStore
    from amadeus.models.state import ProjectRegistryEntry, ProjectState

    project_dir = tmp_path / "test-status"
    project_dir.mkdir()

    state = ProjectState(project_name="test-status", display_name="Test Status", main_goal="Goal")
    store = ProjectStateStore()
    store.save(state, project_dir)

    mock_registry.register(
        ProjectRegistryEntry(
            project_name="test-status",
            display_name="Test Status",
            project_path=str(project_dir),
            is_active=True,
        )
    )

    result = main(["status"])
    assert result == 0
    captured = capsys.readouterr()
    assert "test-status" in captured.out


def test_projects_command_lists_all(mock_registry, capsys):
    from amadeus.models.state import ProjectRegistryEntry

    mock_registry.register(
        ProjectRegistryEntry(project_name="p1", display_name="P1", project_path="/p1")
    )
    mock_registry.register(
        ProjectRegistryEntry(project_name="p2", display_name="P2", project_path="/p2")
    )

    result = main(["projects"])
    assert result == 0
    captured = capsys.readouterr()
    assert "p1" in captured.out
    assert "p2" in captured.out


def test_use_command_switches_active(mock_registry):
    from amadeus.models.state import ProjectRegistryEntry

    mock_registry.register(
        ProjectRegistryEntry(
            project_name="p1", display_name="P1", project_path="/p1", is_active=True
        )
    )
    mock_registry.register(
        ProjectRegistryEntry(
            project_name="p2", display_name="P2", project_path="/p2", is_active=False
        )
    )

    result = main(["use", "p2"])
    assert result == 0
    assert mock_registry.get_active().project_name == "p2"
