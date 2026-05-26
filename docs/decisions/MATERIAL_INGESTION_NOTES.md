# Material Ingestion Notes

Status: isolated spike on branch `codex/material-ingestion-spike`.

Worktree: `C:\tmp\amadeus-material-ingestion`

## Scope

- Added `amadeus/core/material_ingestion.py` only as an isolated converter core.
- Added `amadeus/tests/test_material_ingestion.py` with tests that do not call Ollama and do not need network access.
- Did not wire material ingestion into CLI, workflow, state store, gap analysis, readiness, validator, or generator.
- Did not touch the current State/Gap/Readiness core.

## Contract Draft

Each ingestion call returns a `MaterialIngestionResult` with:

- `source_id`
- `original_path`
- `context_path`
- `status`
- `extraction_notes`

Current statuses:

- `ingested`
- `dependency_missing`
- `adapter_stub`
- `unsupported_type`
- `missing_source`
- `failed`

## Implemented Behavior

- `.txt`, `.md`, and `.markdown` files are converted into deterministic Markdown context files.
- `source_id` values are normalized before they are used as file names.
- Missing sources, unsupported file types, dependency gaps, and adapter stubs return structured results instead of mutating the existing Amadeus workflow.
- PDF and DOCX are intentionally adapter stubs. They require `pypdf` and `python-docx` respectively before real extraction can be enabled, and the spike reports clear failure notes when those dependencies are absent.

## Verification

Commands run from `C:\tmp\amadeus-material-ingestion` using the existing project venv:

- `python -m pytest amadeus/tests/test_material_ingestion.py -q` -> 10 passed.
- `python -m pytest amadeus/tests -q` -> 18 passed.
- `python -m ruff check amadeus/core/material_ingestion.py amadeus/tests/test_material_ingestion.py` -> passed.
- `python -m ruff check amadeus .github pyproject.toml` -> passed.

The tests use temporary local files only. They do not call Ollama and do not require network access.

Note: the older combined command `python -m pytest amadeus/tests study_agent/tests -q` is not applicable in this worktree because `study_agent/tests` is not present.

## Diff Summary

New files only:

- `amadeus/core/material_ingestion.py`
- `amadeus/tests/test_material_ingestion.py`
- `amadeus/docs/decisions/MATERIAL_INGESTION_NOTES.md`

No commit or push was performed. The files were marked with `git add --intent-to-add` so `git diff` shows the full patch without staging content for commit.

Forbidden files intentionally not touched:

- CLI entry points
- workflow/generator/gap/readiness/state/validator core
- `amadeus/models/state.py`
- status/roadmap files
- `amadeus/dev_journey/**`

## Integration Note For Next Codex

The next task should decide where material-derived context belongs in the existing readiness flow:

1. Material ingestion should probably run before gap analysis so missing or failed material extraction can become explicit blockers.
2. Successful `context_path` files can be referenced from Project State once the state schema is extended deliberately.
3. PDF/DOCX extraction should be implemented behind the existing adapter functions, then tests should be expanded with small fixture files.
4. Only after the above contract is accepted should CLI/workflow integration touch `amadeus/main.py`, `amadeus/core/workflow.py`, `amadeus/core/gap_analysis.py`, or `amadeus/models/state.py`.

Recommended next goal: integrate this converter contract into the Amadeus workflow in a separate branch, starting with state/gap/readiness contract changes and only then CLI flags or user-facing commands.
