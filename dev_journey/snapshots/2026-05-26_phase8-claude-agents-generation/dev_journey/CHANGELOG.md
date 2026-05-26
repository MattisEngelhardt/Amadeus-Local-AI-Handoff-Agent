# Amadeus Changelog

This changelog records meaningful project-level changes. It complements `PROJECT_STATUS.md` and the immutable-ish snapshots under `dev_journey/snapshots/`.

## 2026-05-26 - CLAUDE.md & AGENTS.md Generation (Phase 8)

Changed:

- Rewrote `TARGET_CLAUDE_TEMPLATE.md` with all 10 mandatory pillars.
- Rewrote `TARGET_AGENTS_TEMPLATE.md` with full Codex-compatible anatomy.
- Updated the generator to inject rich project state data into templates.
- Added `CLAUDE.md` and `AGENTS.md` anatomy validators.
- Added tests for anatomy validation and generated handoff file quality.

Verified:

- `python -m pytest tests -q`
- `python -m ruff check .`
- `python -m amadeus build-text --output-dir C:\tmp\phase8-test --project-name phase8-handoff --text "Build a CLI tool that processes CSV files and generates summary reports with charts"`

Note:

- The documented `.venv` path was not present in this checkout, so verification
  used the available `python` interpreter.

## 2026-05-26 - Workspace Builder & Material Ingestion

Changed:

- Integrated `material_ingestion.py` spike into the core workflow.
- Extended the gap analysis to detect missing or failed materials.
- Updated the generator to populate `SOURCE_MAP.md` and `CONTEXT_INDEX.md` with extracted material data.
- Implemented `create_workspace_snapshot` in `versioning.py` to create a `_versions/` snapshot after build.
- Added `validate_workspace` to check the generated handoff workspace for canonical files and valid source map references.
- Added `--materials` parameter to the CLI for ingesting files.
- Added integration tests for versioning, validation, and material gap analysis.
- Created a robust GitHub Actions CI pipeline (`.github/workflows/ci.yml`) to automatically run `ruff` and `pytest` (using `xvfb` and `libportaudio2` for headless environment compatibility) on PRs and pushes to main.
- Created a Pull Request template (`.github/pull_request_template.md`) to enforce local verification, quality criteria, and blueprint alignment for all future pull requests.

Verified:

- All tests pass (`pytest amadeus/tests`).
- Smoke tests running against local Gemma 4 via Ollama successfully ingested materials and generated complete workspaces with real version snapshots.

## 2026-05-25 - Project State And Readiness Gate

Changed:

- Added persistent project state schema with phase transitions, raw input
  records, transcript metadata, materials, links, decisions, gaps, prompt
  versions, workspace plan, and readiness snapshot.
- Added deterministic gap analysis for thin goals, referenced-but-missing
  materials, assumptions, optional improvements, targeted questions, and
  readiness scoring.
- Added readiness gate rendering and enforcement before workspace builds.
- Added shared workflow orchestration used by CLI and desktop speechbar path.
- Updated generated handoff files so `PROJECT_BRIEF.md`, `MASTER_PROMPT.md`,
  `DECISIONS.md`, `CONTEXT_INDEX.md`, `SOURCE_MAP.md`, and `_logs/raw_input.md`
  reflect project state where available.
- Added CLI support for documented readiness waivers:
  `--approve-readiness --approval-note "..."`.
- Added tests for successful builds, blocked builds, and approved builds with
  waived blockers.

Verified:

- `.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q`
- `.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml`
- `.\.venv\Scripts\python.exe -m amadeus check-runtime`
- `.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-smoke --project-name readiness-smoke-handoff --text "..."`
- `.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-block --project-name readiness-block-handoff --text "...attached PDF file..."`
- `.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-approved --project-name readiness-approved-handoff --text "...attached PDF file..." --approve-readiness --approval-note "..."`

Notes:

- The missing-PDF smoke intentionally blocks the build and writes a review
  package under `_logs/`.
- The approved missing-PDF smoke builds only after recording the explicit waiver
  note in state and generated decisions.

## 2026-05-24 - Local Gemma Runtime Milestone

Changed:

- Installed and verified Ollama locally.
- Pulled `gemma4:e4b`.
- Added `amadeus/Modelfile`.
- Created the working local Ollama model `amadeus` / `amadeus:latest`.
- Added a stdlib Ollama client and CLI entrypoint under `python -m amadeus`.
- Refactored imports from `speech_to_code.*` to `amadeus.*`.
- Replaced cloud LLM analysis with local Ollama/Gemma analysis.
- Replaced production code generation with handoff workspace generation.
- Made local `faster-whisper` the default transcription path.
- Preloaded `faster-whisper-large-v3` into the local Hugging Face cache.
- Updated tests, config, requirements, and GitHub Actions for the Amadeus path.

Verified:

- `python -m amadeus check-runtime`
- `python -m pytest amadeus/tests study_agent/tests -q`
- `python -m ruff check amadeus .github pyproject.toml`
- `python -m amadeus build-text ...`

Notes:

- The reliable local model name is `amadeus`, which appears in Ollama as
  `amadeus:latest`.
- `amadeus:local` appeared in `ollama list` but did not generate reliably on
  this machine, so runtime config uses `amadeus`.

## 2026-05-24 - Documentation Cleanup And Project Brain

Changed:

- Root documentation was reorganized around the current Amadeus target architecture.
- `CLAUDE.md` was added as the primary project brain.
- `AGENTS.md` was added as Codex-compatible repository instructions.
- `README.md` and `REQUIREMENTS.md` were rewritten to reflect Amadeus as a local Gemma 4 E4B prep agent.
- `PROJECT_STATUS.md`, `DOCUMENTATION_INDEX.md`, and `IMPLEMENTATION_ROADMAP.md` were added.
- Legacy local-AI, Qwen, llama.cpp, and cloud-provider research was moved under `docs/research/`.
- The historical cleanup plan was moved under `docs/decisions/`.
- Target workspace templates were added under `docs/templates/`.
- `dev_journey/` was added to preserve future fallback snapshots and show the development path.

Not changed:

- Python implementation.
- `config.yaml`.
- `requirements.txt`.
- Runtime provider behavior.

Reason:

The repository needed a clean canonical architecture before implementation refactoring.

## 2026-05-24 - README Workflow Visual

Changed:

- Added `assets/amadeus_workflow_overview.svg`.
- Updated `README.md` to show Amadeus' full input, local preparation, readiness gate, workspace, and handoff workflow.

Reason:

The public README needed a clearer recruiter-facing visual that explains Amadeus as a local AI handoff agent rather than a generic voice-to-code tool.
