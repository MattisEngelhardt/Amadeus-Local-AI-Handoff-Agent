import os

from amadeus.core.scaffolder import CANONICAL_DIRECTORIES, ProjectScaffolder
from amadeus.models.project import ProjectFileModel
from amadeus.models.requirements import RequirementsModel


def test_project_scaffolding_creates_handoff_workspace(tmp_path):
    reqs = RequirementsModel(
        project_name="test-scaffold-project",
        display_name="Test Scaffold Project",
        short_description="A dummy handoff workspace.",
        project_type="AI handoff workspace",
        tech_stack=[],
        dependencies=[],
        specifications=["Should create handoff files"],
        quality_criteria=["Clean structure"],
        files_to_create=[],
    )
    generated_files = [
        ProjectFileModel(file_path="MASTER_PROMPT.md", content="# Prompt", purpose="Prompt"),
        ProjectFileModel(file_path="CLAUDE.md", content="# Brain", purpose="Claude brain"),
        ProjectFileModel(file_path="../escape.txt", content="bad", purpose="Traversal attempt"),
    ]

    project_path = ProjectScaffolder(base_output_dir=str(tmp_path)).scaffold(reqs, generated_files)

    assert project_path is not None
    assert os.path.basename(project_path) == "test-scaffold-project"
    assert os.path.exists(os.path.join(project_path, "MASTER_PROMPT.md"))
    assert os.path.exists(os.path.join(project_path, "CLAUDE.md"))
    assert not os.path.exists(os.path.join(tmp_path, "escape.txt"))
    for directory in CANONICAL_DIRECTORIES:
        assert os.path.isdir(os.path.join(project_path, directory))
