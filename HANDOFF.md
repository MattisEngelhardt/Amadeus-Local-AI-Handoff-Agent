# Phase 13-15 Implementation Handoff

**Date:** 2026-05-28
**Status:** In progress — code written, tests need fixing, docs/tag/push pending.

## What Was Done

### Phase 13: Intake Inbox and Project Registry ✅ Code Complete

**New files:**
- `core/inbox.py` — Input registration with stable IDs, content digest, duplicate detection, raw input storage to `_logs/raw_inputs/`
- `tests/test_inbox.py` — 9 tests for text/file input registration, duplicate detection, raw storage

**Modified files:**
- `models/state.py` — `RawInputRecord` extended with `file_path`, `is_duplicate`, `duplicate_of`, new input kinds (`image`, `old_prompt`, `correction`). `MaterialRecord` got `extraction_confidence` and `page_count`. `ProjectRegistryEntry` got `is_archived` and `input_count`.
- `core/project_registry.py` — Added `archive()`, `find_similar_names()`, `get_by_name()`. `list_projects()` now filters archived by default. `update_state()` tracks `input_count`.
- `core/cli.py` — `run_new_command` and `run_add_command` now register inputs via inbox. Added `run_archive_command`, `run_inbox_command`, `run_transcribe_command`.
- `__main__.py` — Registered `archive`, `inbox`, `transcribe` subcommands.

### Phase 14: Voice Pipeline Infrastructure ✅ Code Complete

**New files:**
- `core/voice_pipeline.py` — `transcribe_audio()` with faster-whisper, model fallback, German language, timestamps, uncertainty markers. `write_transcript_artifacts()` writes `_logs/transcripts/<timestamp>_raw.md` and `_clean.md`. `_basic_clean()` removes German fillers. `add_transcript_to_state()` records transcript in project state.
- `tests/test_voice_pipeline.py` — 5 tests for filler cleanup, audio path normalization, transcript artifact writing, uncertain terms.

**CLI:** `amadeus transcribe <audio-file> --model-size large-v3 --language de`

### Phase 15: Material Ingestion V2 ✅ Code Complete

**Modified files:**
- `core/material_ingestion.py` — Complete rewrite:
  - **PDF extraction** now real via `pypdf` (page-by-page text, page count, confidence scoring)
  - **DOCX extraction** now real via `python-docx` (headings→markdown, paragraphs, tables, metadata)
  - **`ingest_image()`** — new function for PNG/JPG/WEBP/etc, reads dimensions via Pillow, creates context md, marks as partial requiring manual review
  - **`ingest_link()`** — new function, stores URL+purpose, creates context md, marks as partial (no auto-fetch)
  - `MaterialIngestionResult` extended with `extraction_confidence` and `page_count`
  - `IMAGE_SUFFIXES` constant added
- `core/workflow.py` — `_ingest_materials()` now routes images to `ingest_image()`, passes confidence/page_count to MaterialRecord
- `requirements.txt` — Added `pypdf>=4.0.0` and `python-docx>=1.0.0`
- `tests/test_material_ingestion_v2.py` — 8 tests: real PDF, real DOCX (with tables), image ingestion, link ingestion, text still works, missing source

**Dependencies installed:** `pypdf` (6.12.2) installed. `python-docx` needs install.

## What's Left

### Immediate (before v6.0.0):

1. **Fix old tests** — `tests/test_material_ingestion.py` has 4 failures:
   - `test_unsupported_material_type_returns_clear_result` — ✅ Fixed (removed old stub assertion)
   - `test_pdf_adapter_remains_explicit_stub_when_dependency_exists` — ✅ Fixed (tests real adapter now)
   - `test_docx_adapter_remains_explicit_stub_when_dependency_exists` — ✅ Fixed (tests real adapter now)
   - `test_result_can_be_serialized_for_future_state_integration` — ❌ STILL NEEDS FIX: `as_dict()` now includes `extraction_confidence` and `page_count` fields. Update the assertion to include them.

2. **Install python-docx** — `pip install python-docx` (was in requirements.txt but pip output only showed pypdf installed)

3. **Run full test suite** — `python -m pytest tests -q` — must pass clean

4. **Run ruff** — `python -m ruff check .`

5. **Update PROJECT_STATUS.md** — Mark Phase 13/14/15 as implemented, update Known Gaps, update Next Priorities

6. **Update IMPLEMENTATION_ROADMAP.md** — Add status lines to Phase 13, 14, 15

7. **Commit, tag v6.0.0, push to GitHub**

### The serialization test fix needed:

In `tests/test_material_ingestion.py`, line ~130, update the dict assertion:
```python
assert result.as_dict() == {
    "source_id": "state-note",
    "original_path": str(source.resolve()),
    "context_path": str(tmp_path / "context" / "state-note.md"),
    "status": "ingested",
    "extraction_notes": ["Plain text material ingested as UTF-8."],
    "extraction_confidence": 1.0,
    "page_count": None,
}
```

## Architecture Notes

- Inbox system stores every raw input with provenance BEFORE any model analysis
- Duplicate detection is content-digest based (SHA-256)
- Voice pipeline uses faster-whisper directly, no cloud API
- PDF/DOCX are real extractors now, not stubs
- Images create partial context (needs vision model or manual review)
- Links are registered but not auto-fetched (safety)
- All new features follow the existing pattern: Pydantic models → core logic → CLI → tests
