from __future__ import annotations

import hashlib
import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

MaterialIngestionStatus = Literal[
    "ingested",
    "dependency_missing",
    "adapter_stub",
    "unsupported_type",
    "missing_source",
    "failed",
]

TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
PDF_SUFFIXES = {".pdf"}
DOCX_SUFFIXES = {".docx"}


class MaterialIngestionError(RuntimeError):
    """Base error for expected material ingestion failures."""


class MissingMaterialDependency(MaterialIngestionError):
    """Raised when an optional adapter dependency is not installed."""


class MaterialAdapterStub(MaterialIngestionError):
    """Raised when an adapter is intentionally scaffolded but not implemented."""


class UnsupportedMaterialType(MaterialIngestionError):
    """Raised when no adapter exists for the source material type."""


@dataclass(frozen=True)
class MaterialIngestionResult:
    source_id: str
    original_path: str
    context_path: str | None
    status: MaterialIngestionStatus
    extraction_notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "original_path": self.original_path,
            "context_path": self.context_path,
            "status": self.status,
            "extraction_notes": list(self.extraction_notes),
        }


def ingest_material(
    source_path: str | Path,
    context_dir: str | Path,
    source_id: str | None = None,
) -> MaterialIngestionResult:
    """Convert one local source file into a deterministic Amadeus context file.

    This is deliberately not wired into the current workflow yet. It is a tested
    converter core that can be integrated once the State/Gap/Readiness contract is
    ready to accept material-derived context.
    """

    source = Path(source_path)
    resolved_original = _safe_resolve(source)
    normalized_source_id = normalize_source_id(source_id or _build_source_id(source))

    if not source.exists():
        return MaterialIngestionResult(
            source_id=normalized_source_id,
            original_path=str(resolved_original),
            context_path=None,
            status="missing_source",
            extraction_notes=("Source material does not exist.",),
        )

    if not source.is_file():
        return MaterialIngestionResult(
            source_id=normalized_source_id,
            original_path=str(resolved_original),
            context_path=None,
            status="failed",
            extraction_notes=("Source material is not a file.",),
        )

    try:
        extracted_text, notes = _extract_text(source)
    except MissingMaterialDependency as exc:
        return _failure_result(
            normalized_source_id,
            resolved_original,
            "dependency_missing",
            str(exc),
        )
    except MaterialAdapterStub as exc:
        return _failure_result(normalized_source_id, resolved_original, "adapter_stub", str(exc))
    except UnsupportedMaterialType as exc:
        return _failure_result(
            normalized_source_id,
            resolved_original,
            "unsupported_type",
            str(exc),
        )
    except UnicodeDecodeError as exc:
        return _failure_result(
            normalized_source_id,
            resolved_original,
            "failed",
            f"Text material must be UTF-8 encoded: {exc}",
        )

    context_root = Path(context_dir)
    context_root.mkdir(parents=True, exist_ok=True)
    context_path = context_root / f"{normalized_source_id}.md"
    context_path.write_text(
        _format_context_document(
            source_id=normalized_source_id,
            original_path=resolved_original,
            extracted_text=extracted_text,
        ),
        encoding="utf-8",
    )

    return MaterialIngestionResult(
        source_id=normalized_source_id,
        original_path=str(resolved_original),
        context_path=str(context_path),
        status="ingested",
        extraction_notes=tuple(notes),
    )


def normalize_source_id(source_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", source_id.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:96] or "material"


def _build_source_id(source_path: Path) -> str:
    stem = normalize_source_id(source_path.stem)
    if source_path.exists() and source_path.is_file():
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:12]
    else:
        digest = hashlib.sha256(str(source_path).encode("utf-8")).hexdigest()[:12]
    return f"{stem}-{digest}"


def _extract_text(source: Path) -> tuple[str, tuple[str, ...]]:
    suffix = source.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _extract_plain_text(source)
    if suffix in PDF_SUFFIXES:
        return _extract_pdf_text(source)
    if suffix in DOCX_SUFFIXES:
        return _extract_docx_text(source)

    raise UnsupportedMaterialType(
        f"Unsupported material type '{suffix or '<none>'}'. Supported now: .md, .markdown, .txt. "
        "PDF and DOCX are scaffolded adapter stubs only."
    )


def _extract_plain_text(source: Path) -> tuple[str, tuple[str, ...]]:
    raw_text = source.read_text(encoding="utf-8")
    text = _normalize_extracted_text(raw_text)
    notes = ["Plain text material ingested as UTF-8."]
    if not text:
        notes.append("No non-whitespace text was extracted.")
    return text, tuple(notes)


def _extract_pdf_text(_source: Path) -> tuple[str, tuple[str, ...]]:
    _require_optional_dependency(
        module_name="pypdf",
        package_name="pypdf",
        material_type="PDF",
    )
    raise MaterialAdapterStub(
        "PDF adapter dependency is present, but PDF extraction is intentionally not implemented "
        "in this isolated spike."
    )


def _extract_docx_text(_source: Path) -> tuple[str, tuple[str, ...]]:
    _require_optional_dependency(
        module_name="docx",
        package_name="python-docx",
        material_type="DOCX",
    )
    raise MaterialAdapterStub(
        "DOCX adapter dependency is present, but DOCX extraction is intentionally not implemented "
        "in this isolated spike."
    )


def _require_optional_dependency(module_name: str, package_name: str, material_type: str) -> None:
    try:
        importlib.import_module(module_name)
    except ImportError as exc:
        raise MissingMaterialDependency(
            f"{material_type} ingestion requires optional dependency '{package_name}'. "
            "Install it before enabling this adapter."
        ) from exc


def _normalize_extracted_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    normalized = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", normalized)


def _format_context_document(source_id: str, original_path: Path, extracted_text: str) -> str:
    body = extracted_text or "_No extractable text content._"
    return (
        f"# Material Context: {source_id}\n\n"
        f"- Source ID: `{source_id}`\n"
        f"- Original path: `{original_path}`\n\n"
        "## Extracted Text\n\n"
        f"{body}\n"
    )


def _failure_result(
    source_id: str,
    original_path: Path,
    status: MaterialIngestionStatus,
    note: str,
) -> MaterialIngestionResult:
    return MaterialIngestionResult(
        source_id=source_id,
        original_path=str(original_path),
        context_path=None,
        status=status,
        extraction_notes=(note,),
    )


def _safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()
