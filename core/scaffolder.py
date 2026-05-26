from __future__ import annotations

import logging
import os
import shutil
from typing import Iterable

from amadeus.models.project import ProjectFileModel
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectState

logger = logging.getLogger(__name__)


CANONICAL_DIRECTORIES = ["_context", "_sources", "_skills", "_versions", "_logs"]


class ProjectScaffolder:
    def __init__(self, base_output_dir: str = "./output") -> None:
        self.base_output_dir = os.path.abspath(base_output_dir)

    def scaffold(
        self,
        requirements: RequirementsModel,
        generated_files: Iterable[ProjectFileModel],
        state: ProjectState | None = None,
    ) -> str | None:
        project_root = os.path.abspath(
            os.path.join(self.base_output_dir, requirements.project_name)
        )
        logger.info(
            "Scaffolding Amadeus workspace '%s' at %s",
            requirements.display_name,
            project_root,
        )

        try:
            os.makedirs(project_root, exist_ok=True)
            for directory in CANONICAL_DIRECTORIES:
                os.makedirs(os.path.join(project_root, directory), exist_ok=True)

            for file_model in generated_files:
                target_path = os.path.abspath(os.path.join(project_root, file_model.file_path))
                if os.path.commonpath([project_root, target_path]) != project_root:
                    logger.warning(
                        "Skipping unsafe path outside workspace: %s",
                        file_model.file_path,
                    )
                    continue

                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                logger.info("Writing workspace file: %s", file_model.file_path)
                with open(target_path, "w", encoding="utf-8") as handle:
                    handle.write(file_model.content)

            if state:
                sources_dir = os.path.join(project_root, "_sources")
                for material in state.materials:
                    original_name = os.path.basename(material.original_path)
                    dest_path = os.path.join(sources_dir, original_name)
                    # The material.original_path in state is stored as '_sources/filename.ext'
                    # Or if it's the actual path from ingestion, let's just make sure we copy it
                    # if it exists somewhere and is not already in dest_path
                    # Wait, in workflow.py we did: record = MaterialRecord(original_path=f"_sources/{name}")
                    # So it's relative. But wait, if it's relative to project_root, it's already there!
                    # Let's just ensure if original_path is an absolute path, we copy it.
                    if os.path.isabs(material.original_path) and os.path.exists(material.original_path):
                        if not os.path.exists(dest_path) or not os.path.samefile(material.original_path, dest_path):
                            shutil.copy2(material.original_path, dest_path)

            return project_root
        except Exception as exc:
            logger.error("Error during Amadeus workspace scaffolding: %s", exc)
            return None
