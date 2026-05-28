from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from amadeus.models.state import ProjectState, RawInputRecord


def compute_content_digest(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _generate_input_id(kind: str) -> str:
    short = uuid.uuid4().hex[:8]
    return f"{kind}-{short}"


def detect_duplicate(state: ProjectState, digest: str) -> RawInputRecord | None:
    for inp in state.raw_inputs:
        if inp.content_digest and inp.content_digest == digest:
            return inp
    return None


def register_text_input(
    state: ProjectState,
    text: str,
    channel: str = "cli",
    kind: str = "text",
) -> tuple[ProjectState, RawInputRecord]:
    digest = compute_content_digest(text)
    existing = detect_duplicate(state, digest)

    record = RawInputRecord(
        input_id=_generate_input_id(kind),
        channel=channel,
        kind=kind,
        raw_text=text,
        content_digest=digest,
        is_duplicate=existing is not None,
        duplicate_of=existing.input_id if existing else "",
    )

    if existing:
        record.notes.append(f"Duplicate of input {existing.input_id}")

    state.raw_inputs.append(record)
    state.touch()
    return state, record


def register_file_input(
    state: ProjectState,
    file_path: Path,
    channel: str = "cli",
    kind: str = "file",
    purpose: str = "",
) -> tuple[ProjectState, RawInputRecord]:
    content = b""
    if file_path.exists() and file_path.is_file():
        content = file_path.read_bytes()

    digest = compute_content_digest(content)
    existing = detect_duplicate(state, digest)

    record = RawInputRecord(
        input_id=_generate_input_id(kind),
        channel=channel,
        kind=kind,
        file_path=str(file_path),
        content_digest=digest,
        is_duplicate=existing is not None,
        duplicate_of=existing.input_id if existing else "",
    )

    if purpose:
        record.notes.append(f"Purpose: {purpose}")
    if existing:
        record.notes.append(f"Duplicate of input {existing.input_id}")

    state.raw_inputs.append(record)
    state.touch()
    return state, record


def store_raw_input(
    record: RawInputRecord,
    project_path: Path,
    source_file: Path | None = None,
) -> Path:
    raw_dir = project_path / "_logs" / "raw_inputs"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if record.raw_text:
        dest = raw_dir / f"{record.input_id}.md"
        header = (
            f"# Raw Input: {record.input_id}\n\n"
            f"- Channel: {record.channel}\n"
            f"- Kind: {record.kind}\n"
            f"- Received: {record.received_at}\n"
            f"- Digest: {record.content_digest}\n\n"
            "## Content\n\n"
        )
        dest.write_text(header + record.raw_text + "\n", encoding="utf-8")
        return dest

    if source_file and source_file.exists():
        suffix = source_file.suffix
        dest = raw_dir / f"{record.input_id}{suffix}"
        shutil.copy2(source_file, dest)
        meta = raw_dir / f"{record.input_id}.meta.md"
        meta.write_text(
            f"# Raw Input: {record.input_id}\n\n"
            f"- Channel: {record.channel}\n"
            f"- Kind: {record.kind}\n"
            f"- Received: {record.received_at}\n"
            f"- Original: {source_file.name}\n"
            f"- Digest: {record.content_digest}\n",
            encoding="utf-8",
        )
        return dest

    dest = raw_dir / f"{record.input_id}.md"
    dest.write_text(
        f"# Raw Input: {record.input_id}\n\n"
        f"- Channel: {record.channel}\n"
        f"- Kind: {record.kind}\n"
        f"- Received: {record.received_at}\n"
        f"- Note: No content stored\n",
        encoding="utf-8",
    )
    return dest
