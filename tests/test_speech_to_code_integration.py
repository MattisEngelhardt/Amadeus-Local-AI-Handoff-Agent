import os

import numpy as np
import scipy.io.wavfile as wav

from amadeus.core.generator import ProjectGenerator
from amadeus.core.scaffolder import ProjectScaffolder
from amadeus.core.transcriber import AudioTranscriber
from amadeus.core.validator import RequirementsValidator
from amadeus.models.requirements import RequirementsModel


def _requirements() -> RequirementsModel:
    return RequirementsModel(
        project_name="stub-handoff",
        display_name="Stub Handoff",
        short_description="Prepare a workspace for a stub project.",
        project_type="AI handoff workspace",
        tech_stack=["Codex"],
        dependencies=[],
        specifications=["Capture requirements", "Generate agent instructions"],
        quality_criteria=["Keep source assumptions visible"],
        files_to_create=[],
    )


def test_amadeus_core_pipeline_builds_handoff_workspace(tmp_path):
    requirements = RequirementsValidator().validate("Raw input", _requirements())
    generated_files = ProjectGenerator().generate_all_files(requirements)
    project_path = ProjectScaffolder(base_output_dir=str(tmp_path)).scaffold(
        requirements,
        generated_files,
    )

    assert project_path is not None
    expected_files = [
        "CLAUDE.md",
        "AGENTS.md",
        "MASTER_PROMPT.md",
        "PROJECT_BRIEF.md",
        "REQUIREMENTS.md",
        "DECISIONS.md",
        "NEXT_STEPS.md",
        "CONTEXT_INDEX.md",
        "SOURCE_MAP.md",
    ]
    for file_path in expected_files:
        assert os.path.exists(os.path.join(project_path, file_path))

    with open(os.path.join(project_path, "MASTER_PROMPT.md"), encoding="utf-8") as handle:
        assert "You are the executing agent" in handle.read()


def test_local_whisper_transcription_uses_faster_whisper_model(tmp_path):
    transcriber = AudioTranscriber(whisper_local_model="tiny")

    class MockSegment:
        text = "Hallo von Amadeus."

    class MockModel:
        def __init__(self) -> None:
            self.calls = []

        def transcribe(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return [MockSegment()], None

    mock_model = MockModel()
    transcriber._local_model = mock_model

    temp_path = tmp_path / "sample.wav"
    wav.write(str(temp_path), 16000, np.zeros(16000, dtype=np.int16))

    result = transcriber.transcribe(str(temp_path))

    assert result == "Hallo von Amadeus."
    assert mock_model.calls
    called_args, called_kwargs = mock_model.calls[0]
    assert isinstance(called_args[0], np.ndarray)
    assert called_kwargs["language"] == "de"
