# Phase 8 Snapshot: CLAUDE.md And AGENTS.md Generation

Date: 2026-05-26
Status: Phase 8 implementation snapshot

## Purpose

This snapshot preserves the Phase 8 milestone where Amadeus generated rich,
state-aware `CLAUDE.md` and `AGENTS.md` files for target handoff workspaces.

## What Changed

- Rewrote `docs/templates/TARGET_CLAUDE_TEMPLATE.md` around the 10 mandatory
  handoff pillars.
- Rewrote `docs/templates/TARGET_AGENTS_TEMPLATE.md` with concise
  Codex-compatible project instructions.
- Updated `core/generator.py` to inject readiness, phase, approval notes,
  decisions, assumptions, blockers, materials, quicklinks, skills, file maps,
  quality criteria, technical context, and implementation priorities.
- Added `CLAUDE.md` and `AGENTS.md` anatomy validation in
  `core/workspace_validator.py`.
- Added tests for anatomy validation and generated handoff file quality.
- Added a lightweight `amadeus` package path shim so `amadeus.*` imports work
  from this repository root when no editable local environment is present.
- Tightened gap-analysis material detection so future input files, such as
  CSV files processed by a generated CLI, are not mistaken for missing attached
  source material.

## Verification

- `python -m pytest tests -q`
- `python -m ruff check .`
- `python -m amadeus build-text --output-dir C:\tmp\phase8-test --project-name phase8-handoff --text "Build a CLI tool that processes CSV files and generates summary reports with charts"`
- Direct inspection confirmed the generated `CLAUDE.md` includes all 10
  required Phase 8 sections.
- Direct inspection confirmed the generated `AGENTS.md` includes the required
  Codex-compatible sections and implementation priorities.

## Notes

The documented repository `.venv` was not present in this checkout, so
verification used the available `python` interpreter after installing `ruff`.
The generated smoke workspace was written to `C:\tmp\phase8-test\phase8-handoff`.
