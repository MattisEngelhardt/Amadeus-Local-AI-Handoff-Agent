# Snapshot 2026-05-26: Workspace Builder & Material Ingestion (Phase 6 & 7)

## Overview
This snapshot marks the completion of Phase 6 (Material Integration) and Phase 7 (Workspace Builder Enhancement). Amadeus can now ingest `.txt` and `.md` source files, map them into the `_sources/` and `_context/` folders, perform gap analysis reflecting the presence or absence of referenced materials, and cleanly output the complete 9 canonical files with initial version snapshots.

## Key Changes
- Integrated `material_ingestion.py` from the spike into `core/`.
- Extended `workflow.py` to ingest materials right before gap analysis, creating `_sources` and `_context` immediately.
- Extended `GapAnalyzer` to generate explicit blockers when material ingestion fails or referenced materials are missing.
- Implemented `create_workspace_snapshot` in `versioning.py`.
- Added `workspace_validator.py` to check for empty or missing canonical files.
- Generator now injects real extracted data into `SOURCE_MAP.md` and `CONTEXT_INDEX.md`.
- `build-text` command now supports `--materials` list of input files.

## Tests
Added comprehensive test suites for `test_versioning.py`, `test_workspace_validator.py`, and updated `test_readiness_workflow.py`. The `test_material_ingestion.py` spike tests were merged as well.
