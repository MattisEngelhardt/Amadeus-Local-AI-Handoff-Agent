import os
import logging
from typing import List
from speech_to_code.models.requirements import RequirementsModel
from speech_to_code.models.project import ProjectFileModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ProjectScaffolder:
    def __init__(self, base_output_dir="./output"):
        """
        Initialize the Project Scaffolder.
        :param base_output_dir: Root directory where new projects will be created.
        """
        self.base_output_dir = os.path.abspath(base_output_dir)

    def scaffold(self, requirements: RequirementsModel, generated_files: List[ProjectFileModel]):
        """
        Scaffolds the directory structure and writes all file contents.
        :param requirements: Requirements model.
        :param generated_files: List of generated files.
        :return: Absolute path to the scaffolded project directory, or None if failed.
        """
        # Define project root folder path
        project_root = os.path.join(self.base_output_dir, requirements.project_name)
        project_root = os.path.abspath(project_root)

        logger.info(f"Scaffolding project '{requirements.display_name}' at: {project_root}")
        
        try:
            # Create root folder
            os.makedirs(project_root, exist_ok=True)

            for file_model in generated_files:
                # Resolve destination path safely (preventing path traversal)
                target_path = os.path.abspath(os.path.join(project_root, file_model.file_path))
                
                # Check for path traversal attempts
                if not target_path.startswith(project_root):
                    logger.warning(f"Skipping file '{file_model.file_path}': Potential path traversal detected.")
                    continue

                # Ensure parent directories exist
                parent_dir = os.path.dirname(target_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)

                # Write contents
                logger.info(f"Writing file: {file_model.file_path}")
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(file_model.content)

            logger.info(f"Scaffolding completed successfully. Project created at {project_root}")
            return project_root

        except Exception as e:
            logger.error(f"Error during project scaffolding: {e}")
            return None
