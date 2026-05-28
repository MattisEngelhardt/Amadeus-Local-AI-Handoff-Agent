# Amadeus Project Status

Status date: 2026-05-28
Project phase: Phase 15 complete; Inbox, Voice Pipeline, and Material Ingestion V2 implemented.


## Baseline Evaluation Score

**Date:** 2026-05-28
**Phase 10 Baseline Score:** 0.99 (99%)

- **Cases Run:** 14
- **Passed:** 14
- **Failed:** 0
- **Mode:** Deterministic

This score serves as the baseline for evaluating regressions when adding the new agent loop and tool executor in Phase 12.

## Current Canonical Direction

Amadeus is a local Gemma 4 E4B prep agent.

Canonical choices:

- Base LLM: `gemma4:e4b`.
- Local Amadeus model alias: `amadeus` / `amadeus:latest`.
- Runtime: Ollama.
- Transcription: local `faster-whisper`.
- Configured transcription model: `large-v3`.
- Inputs: Telegram and desktop speechbar.
- Output: English-named handoff workspace.
- Handoff targets: Codex, Claude Code, Antigravity.
- Core role: context preparation, prompt compilation, gap analysis, source mapping, workspace build.

Amadeus does not execute the final user task.

## Implementation State

Completed in the current implementation milestone:


- Phase 10: `evals/` module added with deterministic runner, scorer, and 14 test cases.
- Phase 11: `core/project_registry.py` handles multi-project state and active context.
- Phase 11: `__main__.py` includes `amadeus new`, `add`, `status`, `gaps`, `materials`, `build`, `validate`.
- Phase 12: `models/tools.py` and `core/tool_registry.py` define agent tool contracts.
- Phase 12: `core/tool_executor.py` manages sandboxed tool execution.
- Phase 12: `core/agent_loop.py` handles multi-step Gemma interaction with Pydantic JSON validation.
- Phase 13: `core/inbox.py` centralizes raw input registration and duplicate detection.
- Phase 14: `core/voice_pipeline.py` introduces transcription with `faster-whisper`.
- Phase 15: `core/material_ingestion.py` has full PDF/DOCX adapters, image metadata, and link support.

- Package imports now use the `amadeus.*` namespace.
- `amadeus/__main__.py` provides CLI commands:
  - `python -m amadeus check-runtime`
  - `python -m amadeus build-text --text "..."`
  - `python -m amadeus build-text --text "..." --approve-readiness --approval-note "..."`
  - `python -m amadeus build-text --text "..." --materials notes.txt`
  - `python -m amadeus install-commands`
- `Modelfile` defines Amadeus' Ollama identity on top of `gemma4:e4b`.
- `core/ollama_client.py` talks to the local Ollama HTTP API with no cloud LLM provider.
- `core/analyzer.py` sends structured JSON extraction prompts to local Gemma.
- `core/validator.py` enforces the handoff workspace contract deterministically.
- `models/state.py` defines persistent project state, phase, input, material,
  decision, gap, prompt-version, workspace-plan, and readiness schemas.
- `core/state_store.py` writes `_logs/amadeus_state.json`,
  `_logs/gap_analysis.json`, and `_logs/readiness_gate.md`.
- `core/gap_analysis.py` detects thin goals, referenced-but-missing materials,
  assumptions, optional improvements, targeted questions, and readiness score.
- `core/readiness.py` renders and enforces the pre-build readiness gate.
- `core/material_ingestion.py` converts source materials (.txt, .md) to clean Markdown.
- `core/workflow.py` ingests materials, creates `_sources` and `_context`, runs gap analysis, scaffolds, and snapshots.
- `core/generator.py` creates handoff workspace files, populated `SOURCE_MAP.md`, `CONTEXT_INDEX.md`, and `_logs/build_log.md`.
- `core/generator.py` now renders rich `CLAUDE.md` and `AGENTS.md`
  handoff instructions from project state, readiness, materials, decisions,
  quality criteria, and workspace file maps.
- `core/versioning.py` generates an initial snapshot of the workspace upon creation.
- `core/workspace_validator.py` validates the workspace after scaffolding,
  including `CLAUDE.md` and `AGENTS.md` anatomy.
- `core/validation_suite.py` defines `ValidationReport` and `ValidationIssue`
  models plus 7 validators: transcript, prompt, gap analysis, material
  coverage, source map, workspace tree, and handoff anatomy.
- `core/workflow.py` runs the validation suite after workspace scaffolding,
  state persistence, gap logs, readiness logs, and the initial version snapshot.
- Every built workspace now receives `_logs/validation_report.md` and
  `_logs/validation_report.json`.
- `IMPLEMENTATION_ROADMAP.md` now contains the detailed post-Phase-9 completion
  plan from baseline evals through global CLI, tool runtime, inputs, material
  ingestion, memory, Telegram, speechbar, packaging, reliability, and final
  end-to-end acceptance.
- `core/scaffolder.py` creates the canonical workspace folders.
- `core/transcriber.py` defaults to local `faster-whisper` without OpenAI API fallback.
- UI labels and notifications use Amadeus identity.
- `config.yaml` targets Ollama/Gemma and local `faster-whisper`.
- `requirements.txt` no longer requires cloud LLM SDKs for the core path.
- GitHub Actions now includes the Amadeus test suite.

Local runtime installed on this laptop:

- Ollama `0.24.0`.
- `gemma4:e4b` pulled locally, size shown by Ollama as 9.6 GB.
- `amadeus` created from `amadeus/Modelfile` and verified through `/api/generate`.
- `faster-whisper-large-v3` preloaded in the Hugging Face cache.

Runtime note:

- `amadeus:local` was tested, returned 404 on `/api/generate`, and tried to pull
  a manifest through `ollama run`.
- Removing that tag also removed `amadeus:latest`, so it was left in the local
  registry as a non-target tag.
- The working local model name is `amadeus`, which appears as `amadeus:latest`.

## Known Gaps

- Telegram ingestion is not implemented yet.
- Desktop speechbar still needs live microphone UX verification after the core refactor.
- Images are ingested as partial text-metadata only; needs visual LLM extraction or manual review.
- Readiness gate is enforced for CLI and speechbar pipeline builds, but it is not
  yet exposed as a rich interactive review UI.
- Evaluation cases for handoff quality and validator regressions are still pending.

## Current File Authority

Canonical:

- `AMADEUS_WORKFLOW_BLUEPRINT.md`
- `GEMMA_TO_AMADEUS_BLUEPRINT.md`
- `REQUIREMENTS.md`
- `IMPLEMENTATION_ROADMAP.md`
- `CLAUDE.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `DOCUMENTATION_INDEX.md`
- `docs/decisions/ARCHITECTURE_DECISIONS.md`

Current implementation:

- `__main__.py`
- `main.py`
- `Modelfile`
- `config.yaml`
- `requirements.txt`
- `core/`
- `models/`
- `ui/`
- `tests/`

Archived:

- `docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md`
- `docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md`
- `docs/research/originals/LOCAL_AI_PLAN_ORIGINAL.md`
- `docs/research/originals/LOCAL_AI_AGENT_MASTERCLASS_ORIGINAL.md`
- `docs/research/originals/LOCAL_LLM_AGENT_SETUP_ORIGINAL.md`

Project journey:

- `dev_journey/README.md`
- `dev_journey/CHANGELOG.md`
- `dev_journey/RESTORE_GUIDE.md`
- `dev_journey/snapshots/2026-05-24_documentation-cleanup/`
- `dev_journey/snapshots/2026-05-24_local-gemma-runtime/`
- `dev_journey/snapshots/2026-05-25_state-readiness-gate/`
- `dev_journey/snapshots/2026-05-26_workspace-builder-materials/`
- `dev_journey/snapshots/2026-05-26_phase8-claude-agents-generation/`
- `dev_journey/snapshots/2026-05-27_final-roadmap-planning/`

## Verified Commands

From the repository root:

```powershell
python -m pytest tests -q
python -m ruff check .
python -m amadeus build-text --output-dir C:\tmp\phase9-test --project-name phase9-handoff --text "Build a Python REST API that serves weather data from a local SQLite database with authentication and rate limiting"
python -m amadeus build-text --output-dir C:\tmp\phase8-test --project-name phase8-handoff --text "Build a CLI tool that processes CSV files and generates summary reports with charts"
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-smoke --project-name amadeus-smoke-handoff --text "..."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-smoke --project-name readiness-smoke-handoff --text "Build a CLI tool workspace that summarizes study notes into a report and includes verification steps."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-block --project-name readiness-block-handoff --text "Build a report from the attached PDF file and preserve citations."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-approved --project-name readiness-approved-handoff --text "Build a report from the attached PDF file and preserve citations." --approve-readiness --approval-note "Proceed with a text-only handoff now; the missing PDF is documented as a waived blocker."
```

Observed verification:

- Phase 9 full test suite collected 59 tests and passed with the available
  interpreter: `python -m pytest tests -q`.
- Phase 9 Ruff check passed: `python -m ruff check .`.
- Phase 9 smoke build created:
  `C:\tmp\phase9-test\phase9-handoff`.
- The Phase 9 smoke workspace contains `_logs/validation_report.md` and
  `_logs/validation_report.json`.
- The Phase 9 smoke validation report ran all 7 validators and reported
  0 errors, 0 warnings, and 0 info issues.
- Phase 8 unit/integration tests passed with the available interpreter:
  `32 passed`.
- Phase 8 Ruff check passed with the available interpreter.
- Phase 8 smoke build created:
  `C:\tmp\phase8-test\phase8-handoff`.
- The generated smoke `CLAUDE.md` contains all 10 required Phase 8 sections.
- The generated smoke `AGENTS.md` contains the required Codex-compatible
  sections and implementation priorities.
- Runtime check found Ollama, `gemma4:e4b`, and `amadeus`.
- Runtime check generated `Amadeus ready.`
- Unit/integration tests passed: `8 passed`.
- Ruff passed.
- Real local Gemma smoke test created:
  `C:\tmp\amadeus-smoke\amadeus-smoke-handoff`.
- Readiness smoke build created:
  `C:\tmp\amadeus-readiness-smoke\readiness-smoke-handoff`.
- Missing-PDF smoke correctly blocked before build and wrote review logs under:
  `C:\tmp\amadeus-readiness-block\readiness-block-handoff`.
- Missing-PDF smoke with explicit approval built:
  `C:\tmp\amadeus-readiness-approved\readiness-approved-handoff`.

Environment note:

- The documented `.venv` path was not present in this checkout during Phase 8
  verification, so the latest tests and lint were run through the available
  `python` interpreter.

## Next Priorities

1. Phase 16/17: Expose desktop speechbar live microphone and review UX.
2. Phase 20/21: Implement Telegram ingestion.
3. Enhance agent evals (Phase 18) and system memory (Phase 19).
