from pathlib import Path

from amadeus.core.voice_pipeline import (
    TranscriptResult,
    _basic_clean,
    normalize_audio_path,
    write_transcript_artifacts,
)


def test_basic_clean_removes_fillers():
    text = "Ähm also ich möchte eine App bauen ja also genau"
    cleaned = _basic_clean(text)
    assert "ähm" not in cleaned.lower()
    assert "genau" not in cleaned.lower()
    assert "App" in cleaned


def test_normalize_audio_path_valid(tmp_path):
    f = tmp_path / "voice.wav"
    f.write_bytes(b"fake audio")
    result = normalize_audio_path(f)
    assert result == f


def test_normalize_audio_path_invalid_ext(tmp_path):
    f = tmp_path / "file.xyz"
    f.write_bytes(b"data")
    assert normalize_audio_path(f) is None


def test_normalize_audio_path_missing():
    assert normalize_audio_path(Path("/nonexistent.wav")) is None


def test_write_transcript_artifacts(tmp_path):
    result = TranscriptResult(
        raw_text="Ich möchte eine REST API bauen",
        language="de",
        segments=[
            {"start": 0.0, "end": 2.5, "text": "Ich möchte eine REST API bauen"},
        ],
        uncertain_terms=[],
    )
    raw_path, clean_path = write_transcript_artifacts(result, tmp_path, "test-001")
    assert raw_path.exists()
    assert clean_path.exists()
    raw_content = raw_path.read_text(encoding="utf-8")
    assert "REST API" in raw_content
    assert "Segments" in raw_content


def test_write_transcript_with_uncertain_terms(tmp_path):
    result = TranscriptResult(
        raw_text="Build something with Kubernetis",
        language="de",
        segments=[
            {
                "start": 0.0,
                "end": 1.0,
                "text": "Build something with Kubernetis",
                "uncertain": True,
            },
        ],
        uncertain_terms=["Kubernetis"],
    )
    raw_path, clean_path = write_transcript_artifacts(result, tmp_path, "test-002")
    clean_content = clean_path.read_text(encoding="utf-8")
    assert "Uncertain Terms" in clean_content
    assert "Kubernetis" in clean_content
