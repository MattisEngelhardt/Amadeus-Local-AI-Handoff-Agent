from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from amadeus.models.state import ProjectState, TranscriptRecord, utc_now_iso

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".opus", ".webm"}


@dataclass(frozen=True)
class TranscriptResult:
    raw_text: str
    language: str = "de"
    segments: list[dict] = field(default_factory=list)
    uncertain_terms: list[str] = field(default_factory=list)
    raw_path: str = ""
    clean_path: str = ""
    success: bool = True
    error: str = ""


def normalize_audio_path(audio_path: Path) -> Path | None:
    if not audio_path.exists():
        return None
    if audio_path.suffix.lower() not in SUPPORTED_AUDIO:
        return None
    return audio_path


def transcribe_audio(
    audio_path: Path,
    model_size: str = "large-v3",
    language: str = "de",
    fallback_model: str = "base",
) -> TranscriptResult:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return TranscriptResult(
            raw_text="",
            success=False,
            error="faster-whisper is not installed. Install it with: pip install faster-whisper",
        )

    resolved = normalize_audio_path(audio_path)
    if resolved is None:
        return TranscriptResult(
            raw_text="",
            success=False,
            error=f"Audio file not found or unsupported format: {audio_path}",
        )

    try:
        model = WhisperModel(model_size, device="auto", compute_type="auto")
    except Exception:
        logger.warning(
            "Failed to load model '%s', falling back to '%s'", model_size, fallback_model
        )
        try:
            model = WhisperModel(fallback_model, device="auto", compute_type="auto")
        except Exception as exc:
            return TranscriptResult(
                raw_text="",
                success=False,
                error=f"Could not load any whisper model: {exc}",
            )

    try:
        segments_iter, info = model.transcribe(
            str(resolved),
            language=language,
            beam_size=5,
            word_timestamps=True,
        )
    except Exception as exc:
        return TranscriptResult(
            raw_text="",
            success=False,
            error=f"Transcription failed: {exc}",
        )

    segments = []
    text_parts = []
    uncertain = []

    for seg in segments_iter:
        seg_data = {
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        }
        if hasattr(seg, "avg_logprob") and seg.avg_logprob < -1.0:
            seg_data["uncertain"] = True
            uncertain.append(seg.text.strip())
        segments.append(seg_data)
        text_parts.append(seg.text.strip())

    raw_text = " ".join(text_parts)

    return TranscriptResult(
        raw_text=raw_text,
        language=language,
        segments=segments,
        uncertain_terms=uncertain,
    )


def write_transcript_artifacts(
    result: TranscriptResult,
    project_path: Path,
    transcript_id: str,
) -> tuple[Path, Path]:
    transcript_dir = project_path / "_logs" / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    timestamp = utc_now_iso().replace(":", "-")
    raw_path = transcript_dir / f"{timestamp}_raw.md"
    clean_path = transcript_dir / f"{timestamp}_clean.md"

    raw_content = (
        f"# Raw Transcript: {transcript_id}\n\n"
        f"- Language: {result.language}\n"
        f"- Segments: {len(result.segments)}\n\n"
        "## Full Text\n\n"
        f"{result.raw_text}\n\n"
    )
    if result.segments:
        raw_content += "## Segments\n\n"
        for i, seg in enumerate(result.segments, 1):
            uncertain_marker = " [UNCERTAIN]" if seg.get("uncertain") else ""
            raw_content += (
                f"{i}. [{seg['start']:.1f}s - {seg['end']:.1f}s]{uncertain_marker} {seg['text']}\n"
            )

    raw_path.write_text(raw_content, encoding="utf-8")

    clean_text = _basic_clean(result.raw_text)
    clean_content = (
        f"# Cleaned Transcript: {transcript_id}\n\n"
        f"- Language: {result.language}\n"
        f"- Uncertain terms: {len(result.uncertain_terms)}\n\n"
        "## Text\n\n"
        f"{clean_text}\n"
    )
    if result.uncertain_terms:
        clean_content += "\n## Uncertain Terms\n\n"
        for term in result.uncertain_terms:
            clean_content += f"- {term}\n"

    clean_path.write_text(clean_content, encoding="utf-8")

    return raw_path, clean_path


def _basic_clean(text: str) -> str:
    fillers_de = [
        r"\bähm?\b",
        r"\böhm?\b",
        r"\bhm+\b",
        r"\bja\s+also\b",
        r"\balso\s+ja\b",
        r"\bnaja\b",
        r"\bgenau\b",
    ]
    cleaned = text
    for filler in fillers_de:
        cleaned = re.sub(filler, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def add_transcript_to_state(
    state: ProjectState,
    result: TranscriptResult,
    input_id: str,
    raw_path: Path,
    clean_path: Path,
) -> ProjectState:
    import uuid

    transcript_id = f"transcript-{uuid.uuid4().hex[:8]}"
    record = TranscriptRecord(
        transcript_id=transcript_id,
        input_id=input_id,
        raw_transcript_path=str(raw_path),
        cleaned_transcript_path=str(clean_path),
        language=result.language,
        uncertain_terms=result.uncertain_terms,
    )
    state.transcripts.append(record)
    state.touch()
    return state
