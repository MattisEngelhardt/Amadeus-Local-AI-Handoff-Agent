from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import yaml

from amadeus.core.ollama_client import OllamaClient, OllamaUnavailable
from amadeus.models.requirements import RequirementsModel

logger = logging.getLogger(__name__)


AMADEUS_ANALYSIS_SYSTEM_PROMPT = """You are Amadeus, a local Gemma 4 E4B prep agent.

Analyze the user's raw project input and return a JSON object that matches this schema:

{
  "project_name": "english-kebab-case-folder-name",
  "display_name": "Short English project title",
  "short_description": "One or two sentence description of the handoff workspace goal.",
  "project_type": "AI handoff workspace",
  "tech_stack": ["Codex", "Claude Code", "Antigravity"],
  "dependencies": [],
  "specifications": ["specific requirements extracted from the input"],
  "quality_criteria": ["quality rules the executing agent must respect"],
  "files_to_create": [
    {"file_path": "MASTER_PROMPT.md", "purpose": "Compiled task prompt"},
    {"file_path": "PROJECT_BRIEF.md", "purpose": "Short project orientation"}
  ]
}

Rules:
- Do not generate production app code.
- Do not invent missing sources, constraints, or user intent.
- Keep workspace file names in English.
- Preserve open questions as specifications or quality criteria when they affect execution.
- If the input is German, understand it but produce English workspace metadata.
- Output JSON only, without markdown fences.
"""


class TranscriptAnalyzer:
    def __init__(
        self,
        model: str = "amadeus",
        config_path: str | None = None,
        llm_provider: str = "ollama",
        ollama_base_url: str = "http://localhost:11434",
        client: OllamaClient | None = None,
        **_legacy_kwargs: Any,
    ) -> None:
        self.llm_provider = llm_provider
        self.model = model
        self.client = client or OllamaClient(base_url=ollama_base_url)
        self.quality_criteria = self._load_quality_criteria(config_path)

    def _load_quality_criteria(self, config_path: str | None) -> list[str]:
        if not config_path or not os.path.exists(config_path):
            return []

        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                config = yaml.safe_load(handle) or {}
        except Exception as exc:
            logger.warning("Failed to load quality criteria from config: %s", exc)
            return []

        criteria = config.get("quality_criteria", [])
        return [str(item) for item in criteria]

    def analyze(self, transcript_text: str) -> RequirementsModel | None:
        if not transcript_text.strip():
            logger.error("Transcript text is empty.")
            return None

        prompt = self._build_prompt(transcript_text)
        try:
            response_text = self.client.generate(
                prompt=prompt,
                model=self.model,
                system=AMADEUS_ANALYSIS_SYSTEM_PROMPT,
                response_format="json",
                options={"temperature": 0.2},
            )
        except OllamaUnavailable as exc:
            logger.error("Cannot analyze because Ollama is unavailable: %s", exc)
            return None
        except Exception as exc:
            logger.error("Local Gemma analysis failed: %s", exc)
            return None

        try:
            payload = self._parse_json_object(response_text)
            return RequirementsModel(**payload)
        except Exception as exc:
            logger.error("Could not parse Amadeus analysis as RequirementsModel: %s", exc)
            logger.debug("Raw model response: %s", response_text)
            return None

    def _build_prompt(self, transcript_text: str) -> str:
        criteria = "\n".join(f"- {criterion}" for criterion in self.quality_criteria)
        quality_section = (
            f"\nDefault repository quality criteria to carry forward:\n{criteria}\n"
            if criteria
            else ""
        )
        return f"""Raw user input:
{transcript_text}
{quality_section}
Return the structured JSON now."""

    def _parse_json_object(self, response_text: str) -> dict[str, Any]:
        text = response_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            parsed = json.loads(text[start : end + 1])

        if not isinstance(parsed, dict):
            raise TypeError("Expected a JSON object from Amadeus analysis.")
        return parsed


if __name__ == "__main__":
    analyzer = TranscriptAnalyzer()
    result = analyzer.analyze("Build a handoff workspace for a local AI study planner.")
    if result:
        print(result.model_dump_json(indent=2))
