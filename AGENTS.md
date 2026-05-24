# Amadeus Agent Instructions

These are the Codex-compatible working instructions for the Amadeus repository.

## Project Direction

Amadeus is a local Gemma 4 E4B prep agent. It receives raw user inputs, voice notes, files, links, and project context, then prepares a complete AI handoff workspace for Codex, Claude Code, or Antigravity.

Amadeus does not execute the final user project task. It prepares context, prompts, source mappings, decisions, workspace structure, `CLAUDE.md`, `AGENTS.md`, and next-step plans.

## Non-Negotiables

- Use `gemma4:e4b` via Ollama as the target core model.
- Use local `faster-whisper` as the target transcription path.
- Treat Telegram and desktop speechbar as the primary input channels.
- Keep generated workspace file and folder names in English.
- Preserve raw inputs separately from cleaned transcripts and compiled prompts.
- Block workspace build while true blockers remain.
- Do not add cloud LLM providers as required core architecture.
- Do not re-promote Qwen, llama.cpp, Gemini, OpenAI API, Anthropic, Groq, NVIDIA NIM, or OpenRouter as current target choices.
- Do not change `config.yaml` or `requirements.txt` during documentation-only work.

## Source Of Truth

Read in this order for architecture work:

1. `AMADEUS_WORKFLOW_BLUEPRINT.md`
2. `GEMMA_TO_AMADEUS_BLUEPRINT.md`
3. `REQUIREMENTS.md`
4. `IMPLEMENTATION_ROADMAP.md`
5. `PROJECT_STATUS.md`

Use `DOCUMENTATION_INDEX.md` to understand each file's role.

## File Ownership

- Root canonical docs: product and repository truth.
- `docs/decisions/`: architecture decisions and historical cleanup inputs.
- `docs/research/`: archived background research only.
- `docs/templates/`: target handoff templates, not current runtime code.
- `dev_journey/`: Amadeus project history, fallback snapshots, changelog, and restore guide.
- `templates/`: legacy prototype templates; do not use for generated handoff workspaces.
- `core/`, `models/`, `ui/`, `main.py`, `__main__.py`: current Amadeus implementation.
- `tests/`: Amadeus tests for the current implementation.

## Expected Commands

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
```

Current runtime target:

- `gemma4:e4b` is the pulled base model.
- `amadeus` / `amadeus:latest` is the working Ollama model created from `Modelfile`.
- `amadeus:local` may appear in `ollama list`, but do not use it unless re-verified.

Use search-first inspection:

```powershell
rg "pattern" .
rg --files
```

## Edit Discipline

- Keep edits scoped to the requested phase.
- Prefer updating the canonical doc that owns the question instead of duplicating content.
- Preserve legacy research by moving or summarizing it under `docs/research/`.
- When editing generated-workspace templates, keep them English and execution-agent friendly.
- When updating implementation, update tests and status in the same change.
- Before risky canonical documentation or architecture refactors, add a curated snapshot under `dev_journey/snapshots/`.

## Implementation Priorities

1. Ollama/Gemma identity harness.
2. Local transcription path with `faster-whisper`.
3. Commit and push major working milestones to GitHub for fallback.
4. Project state store.
5. Prompt compiler.
6. Gap analysis and readiness gate.
7. Document ingestion and source mapping.
8. Workspace builder expansion for the target handoff contract.
9. Validators and eval suite.

## Definition Of Done

A change is done only when:

- It aligns with the two canonical blueprints.
- It does not revive legacy provider/model assumptions.
- It preserves or routes old research correctly.
- It clearly distinguishes current implementation state from target architecture.
- It updates `dev_journey/CHANGELOG.md` or a snapshot when the change is a meaningful project milestone.
- Tests or verification steps were run, or the reason they were not run is documented.
