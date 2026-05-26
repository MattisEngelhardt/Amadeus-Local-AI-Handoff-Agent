# Amadeus Project Status

Status date: 2026-05-26
Project phase: Material ingestion and Workspace Builder implemented

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
- `core/versioning.py` generates an initial snapshot of the workspace upon creation.
- `core/workspace_validator.py` validates the workspace after scaffolding.
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
- PDF and DOCX extraction are currently mocked adapter stubs and need the actual extraction implementations using `pypdf` and `python-docx`.
- Readiness gate is enforced for CLI and speechbar pipeline builds, but it is not
  yet exposed as a rich interactive review UI.
- Evaluation cases and validators beyond the current handoff contract tests are still pending.

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

## Verified Commands

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-smoke --project-name amadeus-smoke-handoff --text "..."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-smoke --project-name readiness-smoke-handoff --text "Build a CLI tool workspace that summarizes study notes into a report and includes verification steps."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-block --project-name readiness-block-handoff --text "Build a report from the attached PDF file and preserve citations."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-approved --project-name readiness-approved-handoff --text "Build a report from the attached PDF file and preserve citations." --approve-readiness --approval-note "Proceed with a text-only handoff now; the missing PDF is documented as a waived blocker."
```

Observed verification:

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

## Next Priorities

1. Implement real PDF/DOCX extraction inside `material_ingestion.py`.
2. Populate `_skills/` depending on workspace plan configuration (Phase 8).
3. Live-test the desktop speechbar microphone UX against the new readiness flow.
4. Add Telegram ingestion.
5. Expand validators and evaluation cases.
6. Add a richer interactive readiness review/approval surface.
