# Phase 9 Validation Suite Snapshot

Date: 2026-05-27

This snapshot captures the Phase 9 validation-suite milestone for Amadeus.

Phase 9 adds a unified validation layer that runs after workspace scaffolding,
state persistence, gap/readiness logs, and the initial workspace snapshot. The
suite keeps the existing warn-only build behavior while producing structured
Markdown and JSON validation reports under `_logs/`.

Captured files:

- `core/validation_suite.py`: new validation report models, 7 validators, report rendering, report saving, and orchestrator.
- `core/workflow.py`: build-pipeline integration for validation reports.
- `core/workspace_validator.py`: existing legacy workspace and anatomy validators used by the new handoff anatomy validator.

Verification target:

- `python -m pytest tests -q`
- `python -m ruff check .`
- Smoke build with `_logs/validation_report.md` and `_logs/validation_report.json`.
