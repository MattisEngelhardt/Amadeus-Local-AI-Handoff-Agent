# Amadeus Changelog

This changelog records meaningful project-level changes. It complements `PROJECT_STATUS.md` and the immutable-ish snapshots under `dev_journey/snapshots/`.

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
