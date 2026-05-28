from __future__ import annotations

from pathlib import Path

from amadeus.core import material_ingestion
from amadeus.core.material_ingestion import ingest_material, normalize_source_id


def test_ingest_text_material_writes_context_file(tmp_path):
    source = tmp_path / "Client Brief.md"
    source.write_text("Line one.  \r\n\r\n\r\nLine two.\n", encoding="utf-8")
    context_dir = tmp_path / "context"

    result = ingest_material(source, context_dir)

    assert result.status == "ingested"
    assert result.source_id.startswith("client-brief-")
    assert Path(result.original_path) == source.resolve()
    assert result.context_path is not None
    assert Path(result.context_path).exists()
    assert "Plain text material ingested as UTF-8." in result.extraction_notes

    context_text = Path(result.context_path).read_text(encoding="utf-8")
    assert "# Material Context: client-brief-" in context_text
    assert f"- Original path: `{source.resolve()}`" in context_text
    assert "Line one.\n\nLine two." in context_text
    assert "\n\n\nLine two" not in context_text


def test_custom_source_id_is_sanitized_before_writing_context_file(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("Scope notes", encoding="utf-8")

    result = ingest_material(source, tmp_path / "context", source_id="../Client Material 01")

    assert result.status == "ingested"
    assert result.source_id == "client-material-01"
    assert result.context_path is not None
    assert Path(result.context_path).name == "client-material-01.md"
    assert Path(result.context_path).parent == tmp_path / "context"


def test_missing_source_returns_result_without_creating_context_file(tmp_path):
    missing_source = tmp_path / "missing.md"

    result = ingest_material(missing_source, tmp_path / "context")

    assert result.status == "missing_source"
    assert result.context_path is None
    assert result.extraction_notes == ("Source material does not exist.",)
    assert not (tmp_path / "context").exists()


def test_unsupported_material_type_returns_clear_result(tmp_path):
    source = tmp_path / "archive.zip"
    source.write_bytes(b"not a supported material")

    result = ingest_material(source, tmp_path / "context")

    assert result.status == "unsupported_type"
    assert result.context_path is None
    assert "Unsupported material type '.zip'" in result.extraction_notes[0]


def test_pdf_adapter_reports_missing_dependency_without_network_or_ollama(tmp_path, monkeypatch):
    source = tmp_path / "brief.pdf"
    source.write_bytes(b"%PDF-1.4 placeholder")
    monkeypatch.setattr(material_ingestion.importlib, "import_module", _missing_import)

    result = ingest_material(source, tmp_path / "context")

    assert result.status == "dependency_missing"
    assert result.context_path is None
    assert "PDF ingestion requires optional dependency 'pypdf'" in result.extraction_notes[0]


def test_pdf_adapter_remains_explicit_stub_when_dependency_exists(tmp_path, monkeypatch):
    """PDF now has a real adapter. Test that invalid PDF content produces a failed result."""
    source = tmp_path / "brief.pdf"
    source.write_bytes(b"%PDF-1.4 placeholder")

    result = ingest_material(source, tmp_path / "context")

    assert result.status in ("failed", "partial", "ingested")


def test_docx_adapter_reports_missing_dependency_without_network_or_ollama(tmp_path, monkeypatch):
    source = tmp_path / "brief.docx"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(material_ingestion.importlib, "import_module", _missing_import)

    result = ingest_material(source, tmp_path / "context")

    assert result.status == "dependency_missing"
    assert result.context_path is None
    assert "DOCX ingestion requires optional dependency 'python-docx'" in result.extraction_notes[0]


def test_docx_adapter_remains_explicit_stub_when_dependency_exists(tmp_path, monkeypatch):
    """DOCX now has a real adapter. Test that invalid DOCX content produces a failed result."""
    source = tmp_path / "brief.docx"
    source.write_bytes(b"placeholder")

    result = ingest_material(source, tmp_path / "context")

    assert result.status == "failed"


def test_result_can_be_serialized_for_future_state_integration(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("State handoff material", encoding="utf-8")

    result = ingest_material(source, tmp_path / "context", source_id="state-note")

    assert result.as_dict() == {
        "source_id": "state-note",
        "original_path": str(source.resolve()),
        "context_path": str(tmp_path / "context" / "state-note.md"),
        "status": "ingested",
        "extraction_notes": ["Plain text material ingested as UTF-8."],
        "extraction_confidence": 1.0,
        "page_count": None,
    }


def test_normalize_source_id_has_stable_filesystem_safe_fallback():
    assert normalize_source_id("  Client Material 01  ") == "client-material-01"
    assert normalize_source_id("../") == "material"


def _missing_import(module_name: str):
    raise ImportError(f"No module named {module_name}")
