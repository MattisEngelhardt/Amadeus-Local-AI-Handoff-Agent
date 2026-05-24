# Amadeus Project Status

Status date: 2026-05-24
Project phase: Local Gemma/Ollama runtime harness working; deeper agent phases pending

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
  - `python -m amadeus install-commands`
- `Modelfile` defines Amadeus' Ollama identity on top of `gemma4:e4b`.
- `core/ollama_client.py` talks to the local Ollama HTTP API with no cloud LLM provider.
- `core/analyzer.py` sends structured JSON extraction prompts to local Gemma.
- `core/validator.py` enforces the handoff workspace contract deterministically.
- `core/generator.py` now creates handoff workspace files, not production app code.
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
- Project state storage and phase transitions are not implemented yet.
- Gap analysis is currently represented through prompt/quality constraints, not a full schema.
- Material ingestion and PDF/DOCX/TXT/MD conversion are not implemented yet.
- Source map and context index files are generated as empty starter files until materials exist.
- Readiness gate is not yet enforced as an interactive approval flow.
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

## Verified Commands

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-smoke --project-name amadeus-smoke-handoff --text "..."
```

Observed verification:

- Runtime check found Ollama, `gemma4:e4b`, and `amadeus`.
- Runtime check generated `Amadeus ready.`
- Unit/integration tests passed: `5 passed`.
- Ruff passed.
- Real local Gemma smoke test created:
  `C:\tmp\amadeus-smoke\amadeus-smoke-handoff`.

## Next Priorities

1. Commit and push this local Gemma runtime milestone to GitHub as a fallback point.
2. Add project state storage and phase transitions.
3. Implement a real gap analysis schema and readiness gate.
4. Add material ingestion and Markdown conversion for files.
5. Wire desktop speechbar live recording into the new Amadeus pipeline.
6. Add Telegram ingestion.
7. Expand validators and evaluation cases.
