import json

from amadeus.core.analyzer import TranscriptAnalyzer
from amadeus.models.requirements import RequirementsModel


class FakeOllamaClient:
    def __init__(self) -> None:
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return json.dumps(
            {
                "project_name": "local-study-agent",
                "display_name": "Local Study Agent",
                "short_description": "Prepare a handoff workspace for a local study assistant.",
                "project_type": "AI handoff workspace",
                "tech_stack": ["Codex", "Claude Code"],
                "dependencies": [],
                "specifications": ["Prepare context before implementation"],
                "quality_criteria": ["Do not invent missing source material"],
                "files_to_create": [
                    {
                        "file_path": "MASTER_PROMPT.md",
                        "purpose": "Compiled execution prompt",
                    }
                ],
            }
        )


def test_transcript_analysis_uses_local_ollama_client():
    client = FakeOllamaClient()
    analyzer = TranscriptAnalyzer(model="amadeus", client=client)

    result = analyzer.analyze("Ich brauche einen lokalen Study-Agent Workspace.")

    assert isinstance(result, RequirementsModel)
    assert result.project_name == "local-study-agent"
    assert result.project_type == "AI handoff workspace"
    assert result.dependencies == []
    assert client.calls
    assert client.calls[0]["model"] == "amadeus"
    assert client.calls[0]["response_format"] == "json"
