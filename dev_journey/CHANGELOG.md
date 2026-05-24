# Amadeus Changelog

This changelog records meaningful project-level changes. It complements `PROJECT_STATUS.md` and the immutable-ish snapshots under `dev_journey/snapshots/`.

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
