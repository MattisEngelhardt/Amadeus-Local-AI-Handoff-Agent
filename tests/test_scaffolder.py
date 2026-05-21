import os
import tempfile
import shutil
import pytest
from speech_to_code.core.scaffolder import ProjectScaffolder
from speech_to_code.models.requirements import RequirementsModel, FilePlaceholder
from speech_to_code.models.project import ProjectFileModel

@pytest.fixture
def temp_dir():
    # Setup temporary directory for testing filesystem operations
    test_dir = tempfile.mkdtemp()
    yield test_dir
    # Cleanup after test finishes
    shutil.rmtree(test_dir, ignore_errors=True)

def test_project_scaffolding(temp_dir):
    # 1. Arrange mock requirements
    reqs = RequirementsModel(
        project_name="test-scaffold-project",
        display_name="Test Scaffold Project",
        short_description="A dummy test project for scaffolding verification.",
        project_type="Python CLI Tool",
        tech_stack=["Python"],
        dependencies=["pytest"],
        specifications=["Should do nothing"],
        quality_criteria=["Clean code"],
        files_to_create=[
            FilePlaceholder(file_path="main.py", purpose="Entry point"),
            FilePlaceholder(file_path="core/utils.py", purpose="Helpers")
        ]
    )

    # 2. Arrange mock generated files list
    generated_files = [
        ProjectFileModel(
            file_path="main.py",
            content="print('Hello Test Scaffold')",
            purpose="Entry point"
        ),
        ProjectFileModel(
            file_path="core/utils.py",
            content="def helper(): return True",
            purpose="Helpers"
        )
    ]

    # 3. Act
    scaffolder = ProjectScaffolder(base_output_dir=temp_dir)
    project_path = scaffolder.scaffold(reqs, generated_files)

    # 4. Assert
    assert project_path is not None
    assert os.path.exists(project_path)
    
    # Check expected project directory root structure
    assert os.path.basename(project_path) == "test-scaffold-project"
    
    # Check generated files on disk
    main_file_path = os.path.join(project_path, "main.py")
    utils_file_path = os.path.join(project_path, "core", "utils.py")
    
    assert os.path.exists(main_file_path)
    assert os.path.exists(utils_file_path)
    
    with open(main_file_path, "r", encoding="utf-8") as f:
        assert f.read() == "print('Hello Test Scaffold')"
        
    with open(utils_file_path, "r", encoding="utf-8") as f:
        assert f.read() == "def helper(): return True"
