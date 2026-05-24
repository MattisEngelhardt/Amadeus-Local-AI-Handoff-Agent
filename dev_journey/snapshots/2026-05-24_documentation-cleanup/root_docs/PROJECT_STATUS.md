# Amadeus Project Status

Status date: 2026-05-24
Project phase: Documentation cleanup complete, implementation refactor pending

## Current Canonical Direction

Amadeus is a local Gemma 4 E4B prep agent.

Canonical choices:

- LLM: `gemma4:e4b`.
- Runtime: Ollama.
- Transcription: local `faster-whisper`.
- Inputs: Telegram and desktop speechbar.
- Output: English-named handoff workspace.
- Handoff targets: Codex, Claude Code, Antigravity.
- Core role: context preparation, prompt compilation, gap analysis, source mapping, workspace build.

Amadeus does not execute the final user task.

## Documentation State

Completed:

- Root documentation consolidated around the new Amadeus architecture.
- `CLAUDE.md` added as the project brain.
- `AGENTS.md` added as Codex-compatible repository instructions.
- `README.md` rewritten for the current architecture.
- `REQUIREMENTS.md` rewritten as canonical product requirements.
- `DOCUMENTATION_INDEX.md` added.
- `IMPLEMENTATION_ROADMAP.md` added.
- `docs/decisions/ARCHITECTURE_DECISIONS.md` added.
- Target workspace templates added under `docs/templates/`.
- Legacy local-AI research moved out of root and archived under `docs/research/`.
- Full original legacy research files preserved under `docs/research/originals/`.
- `dev_journey/` added for Amadeus' own changelog, restore guide, and curated fallback snapshots.

## Implementation State

The current Python implementation is a prototype and does not yet match the canonical target architecture.

Known mismatches:

- App identity still uses `SpeechToCodeApp`.
- Imports use the `speech_to_code.*` namespace while the folder is named `amadeus`.
- `config.yaml` still defaults to Gemini/Claude/OpenAI-style provider choices.
- `core/analyzer.py`, `core/validator.py`, and `core/generator.py` still use Claude/Gemini cloud paths.
- `core/transcriber.py` supports local `faster-whisper`, but still contains OpenAI API fallback behavior.
- `core/generator.py` generates production code files, which conflicts with the new prep-agent role.
- Existing runtime Jinja templates are not yet the final target workspace templates.
- `requirements.txt` still includes cloud-provider dependencies needed by the legacy prototype.

These mismatches are documented intentionally. They should be fixed during implementation roadmap phases, not during documentation cleanup.

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

Archived:

- `docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md`
- `docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md`
- `docs/research/originals/LOCAL_AI_PLAN_ORIGINAL.md`
- `docs/research/originals/LOCAL_AI_AGENT_MASTERCLASS_ORIGINAL.md`
- `docs/research/originals/LOCAL_LLM_AGENT_SETUP_ORIGINAL.md`

Historical:

- `docs/decisions/AMADEUS_DOCUMENTATION_CLEANUP_PLAN.md`

Project journey:

- `dev_journey/README.md`
- `dev_journey/CHANGELOG.md`
- `dev_journey/RESTORE_GUIDE.md`
- `dev_journey/snapshots/2026-05-24_documentation-cleanup/`

Implementation material:

- `main.py`
- `core/`
- `models/`
- `ui/`
- `templates/`
- `tests/`
- `config.yaml`
- `requirements.txt`

## Next Priorities

1. Refactor the app identity from `speech_to_code` to Amadeus.
2. Replace Claude/Gemini analysis with local Ollama/Gemma calls.
3. Make `faster-whisper` local transcription the real default.
4. Introduce project state storage and phases.
5. Implement prompt compiler and gap analysis schemas.
6. Replace code generation with handoff workspace generation.
7. Generate target `CLAUDE.md` and `AGENTS.md` from templates.
8. Add validators and eval cases.

## Verification Notes

Documentation verification should include:

```powershell
rg -n "Qwen|qwen|DeepSeek|Gemini|OpenAI API|Anthropic|Groq|NVIDIA|OpenRouter|cloud fallback" . -g "*.md"
```

Expected result:

- canonical docs may mention these terms only as legacy, non-core, or explicitly rejected concepts;
- archived docs may contain them as historical research;
- root docs must not present them as target architecture.

Implementation verification is still pending. The current code is expected to need refactoring before all tests can represent the new architecture.
