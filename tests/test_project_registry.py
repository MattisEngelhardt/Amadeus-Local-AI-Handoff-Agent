from amadeus.core.project_registry import ProjectRegistry
from amadeus.models.state import ProjectPhase, ProjectRegistryEntry, ProjectState


def test_register_and_list(tmp_path):
    registry = ProjectRegistry(registry_file=tmp_path / "projects.json")
    e1 = ProjectRegistryEntry(project_name="p1", display_name="P1", project_path="/p1")
    e2 = ProjectRegistryEntry(project_name="p2", display_name="P2", project_path="/p2")
    registry.register(e1)
    registry.register(e2)
    entries = registry.list_projects()
    assert len(entries) == 2
    assert entries[0].project_name == "p1"
    assert entries[1].project_name == "p2"


def test_set_active(tmp_path):
    registry = ProjectRegistry(registry_file=tmp_path / "projects.json")
    e1 = ProjectRegistryEntry(project_name="p1", display_name="P1", project_path="/p1")
    e2 = ProjectRegistryEntry(project_name="p2", display_name="P2", project_path="/p2")
    registry.register(e1)
    registry.register(e2)
    registry.set_active("p2")
    active = registry.get_active()
    assert active.project_name == "p2"


def test_remove(tmp_path):
    registry = ProjectRegistry(registry_file=tmp_path / "projects.json")
    e1 = ProjectRegistryEntry(project_name="p1", display_name="P1", project_path="/p1")
    registry.register(e1)
    registry.remove("p1")
    assert len(registry.list_projects()) == 0


def test_update_state(tmp_path):
    registry = ProjectRegistry(registry_file=tmp_path / "projects.json")
    e1 = ProjectRegistryEntry(
        project_name="p1",
        display_name="P1",
        project_path="/p1",
        phase=ProjectPhase.CONTEXT_COLLECTION,
    )
    registry.register(e1)

    state = ProjectState(project_name="p1", display_name="P1", main_goal="Goal")
    state.phase = ProjectPhase.WORKSPACE_BUILD
    registry.update_state("p1", state)

    entries = registry.list_projects()
    assert entries[0].phase == ProjectPhase.WORKSPACE_BUILD


def test_registry_persists_to_disk(tmp_path):
    registry_file = tmp_path / "projects.json"
    registry1 = ProjectRegistry(registry_file=registry_file)
    e1 = ProjectRegistryEntry(project_name="p1", display_name="P1", project_path="/p1")
    registry1.register(e1)

    registry2 = ProjectRegistry(registry_file=registry_file)
    entries = registry2.list_projects()
    assert len(entries) == 1
    assert entries[0].project_name == "p1"
