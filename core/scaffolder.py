from __future__ import annotations

import logging
import os
from typing import Iterable

from amadeus.models.project import ProjectFileModel
from amadeus.models.requirements import RequirementsModel

logger = logging.getLogger(__name__)


CANONICAL_DIRECTORIES = ["_context", "_sources", "_skills", "_versions", "_logs"]


class ProjectScaffolder:
    def __init__(self, base_output_dir: str = "./output") -> None:
        self.base_output_dir = os.path.abspath(base_output_dir)

    def scaffold(
        self,
        requirements: RequirementsModel,
        generated_files: Iterable[ProjectFileModel],
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

            return project_root
        except Exception as exc:
            logger.error("Error during Amadeus workspace scaffolding: %s", exc)
            return None
