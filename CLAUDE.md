# Amadeus Project Brain

This file is the primary project brain for agents working inside the Amadeus repository.
Read it before editing documentation, code, templates, or runtime configuration.

## 1. Role Alignment

You are working on Amadeus, a local Gemma 4 E4B prep agent.

Amadeus turns raw user intent, voice notes, text messages, files, and links into a complete AI handoff workspace for Codex, Claude Code, or Antigravity. Amadeus prepares the work; it does not execute the user's final project task.

The target outcome of this repository is not a generic code generator. It is a reliable local context, prompt, gap-analysis, and workspace-building system.

## 2. Non-Negotiable Constraints

- Core model: `gemma4:e4b`.
- Runtime: local via Ollama.
- Core transcription: local and free via `faster-whisper`.
- Primary inputs: Telegram and desktop speechbar.
- Handoff targets: Codex, Claude Code, and Antigravity as later executing environments.
- Handoff contract: English file and folder names.
- Amadeus must preserve raw inputs separately from cleaned or compiled context.
- Amadeus must ask targeted questions when blockers remain.
- Amadeus must not silently invent sources, constraints, missing files, or user intent.
- Amadeus must not treat cloud LLM providers as required core architecture.
- Amadeus must not generate productive app/code files as the final user task; it generates specs, prompts, context maps, and workspace instructions.

Legacy-only concepts:

- Qwen as target model.
- llama.cpp as default runtime.
- Gemini, OpenAI API, Anthropic, Groq, NVIDIA NIM, OpenRouter as core providers.
- Cloud fallback as part of the normal Amadeus workflow.
- "Speech-to-code" code generation as the final product.

## 3. Current Project State

Documentation has been consolidated around the new Amadeus architecture.

Canonical product direction exists in:

1. [AMADEUS_WORKFLOW_BLUEPRINT.md](AMADEUS_WORKFLOW_BLUEPRINT.md)
2. [GEMMA_TO_AMADEUS_BLUEPRINT.md](GEMMA_TO_AMADEUS_BLUEPRINT.md)
3. [REQUIREMENTS.md](REQUIREMENTS.md)
4. [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
5. [PROJECT_STATUS.md](PROJECT_STATUS.md)

Important current limitation:

The Python prototype still reflects older `speech_to_code`, Claude/Gemini/OpenAI, and code-generation assumptions. Treat code/config as legacy implementation until the roadmap explicitly refactors it. Do not "fix" config or dependencies during documentation work unless the user asks for implementation changes.

## 4. Canonical Reading Order

For product and workflow work:

1. `AMADEUS_WORKFLOW_BLUEPRINT.md`
2. `GEMMA_TO_AMADEUS_BLUEPRINT.md`
3. `REQUIREMENTS.md`
4. `IMPLEMENTATION_ROADMAP.md`
5. `PROJECT_STATUS.md`

For repository/documentation navigation:

1. `DOCUMENTATION_INDEX.md`
2. `CLAUDE.md`
3. `AGENTS.md`
4. `docs/decisions/ARCHITECTURE_DECISIONS.md`

For legacy research:

1. `docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md`
2. `docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md`
3. `docs/research/originals/`

Use archived files only for background patterns. Never let archived model/provider choices override the canonical blueprints.

## 5. Semantic File Map

Root project brain:

- `CLAUDE.md`: primary state and instruction file for Claude Code and similar agents working on this repository.
- `AGENTS.md`: Codex-compatible working instructions for this repository.
- `README.md`: human-facing overview of Amadeus.
- `PROJECT_STATUS.md`: current canonical status, implementation gaps, and next work.
- `DOCUMENTATION_INDEX.md`: map of every important document and its authority.

Canonical architecture:

- `AMADEUS_WORKFLOW_BLUEPRINT.md`: detailed target workflow from input to final handoff workspace.
- `GEMMA_TO_AMADEUS_BLUEPRINT.md`: behavior architecture for turning `gemma4:e4b` into Amadeus.
- `REQUIREMENTS.md`: product requirements aligned with the two blueprints.
- `IMPLEMENTATION_ROADMAP.md`: build phases and acceptance gates.

Supporting documentation:

- `docs/decisions/ARCHITECTURE_DECISIONS.md`: current architecture decisions and rationale.
- `docs/decisions/AMADEUS_DOCUMENTATION_CLEANUP_PLAN.md`: historical cleanup plan that shaped this structure.
- `docs/templates/TARGET_CLAUDE_TEMPLATE.md`: template for generated target workspaces.
- `docs/templates/TARGET_AGENTS_TEMPLATE.md`: template for generated target workspaces.
- `docs/research/`: preserved research and legacy notes.
- `dev_journey/`: project history, changelog, restore guide, and curated fallback snapshots for Amadeus itself.

Runtime implementation:

- `main.py`: current prototype application entrypoint; still legacy-oriented.
- `core/`: recorder, transcriber, analyzer, validator, generator, scaffolder modules.
- `models/`: Pydantic models for the current prototype.
- `templates/`: current runtime Jinja templates; not yet aligned with the new target workspace contract.
- `tests/`: prototype tests for the current implementation.
- `config.yaml`: current runtime config; known mismatch with target architecture.
- `requirements.txt`: current dependencies; includes legacy cloud-provider packages.

## 6. Architecture Decisions

The current decisions are summarized in `docs/decisions/ARCHITECTURE_DECISIONS.md`.

Highest-level decisions:

- Amadeus is local-first, not cloud-first.
- Gemma 4 E4B via Ollama is the core LLM.
- `faster-whisper` is the default transcription path.
- Telegram and desktop speechbar are the primary inputs.
- The system builds handoff workspaces, not final deliverables.
- `CLAUDE.md` is the brain of generated Claude Code workspaces.
- `AGENTS.md` is the Codex-compatible entrypoint.
- Legacy research stays archived but non-canonical.

## 7. Work Rules

Before editing documentation:

1. Check `DOCUMENTATION_INDEX.md`.
2. Identify whether the target file is canonical, status, roadmap, template, research, or legacy.
3. Preserve useful old knowledge in `docs/research/` instead of deleting it blindly.
4. Keep root docs concise and routing-focused.
5. Do not reintroduce Qwen/cloud-provider assumptions into canonical files.
6. For substantial changes to canonical docs, create or update a `dev_journey/` snapshot.

Before editing code:

1. Read `PROJECT_STATUS.md` and `IMPLEMENTATION_ROADMAP.md`.
2. Identify whether the change belongs to the documentation cleanup or an implementation phase.
3. Do not update `config.yaml` or `requirements.txt` opportunistically.
4. Keep code changes aligned with the target architecture: Ollama/Gemma, faster-whisper, state store, prompt compiler, gap analysis, workspace builder.
5. Add or update tests when behavior changes.

Before adding a provider:

1. Verify the request does not violate the no-cloud-core constraint.
2. If optional manual review/export is needed, document it as a non-core fallback.
3. Do not add provider switching as the default architecture.

## 8. Quality Rubric

A correct Amadeus change:

- Aligns with both canonical blueprints.
- Separates current target architecture from legacy implementation state.
- Improves the future executing agent's ability to work without missing context.
- Keeps raw inputs, cleaned context, source maps, and decisions distinct.
- Uses English file and folder names for generated workspaces.
- Adds validation or test coverage for behavior changes.
- Leaves archived research clearly marked as non-canonical.

An incorrect Amadeus change:

- Treats Amadeus as the final code-writing agent.
- Makes a cloud provider required for the core workflow.
- Makes Qwen or llama.cpp the current target.
- Deletes old research without preserving the useful lesson.
- Bloats `CLAUDE.md` with full research notes instead of routing to deeper docs.
- Hides blockers as assumptions.

## 9. Micro-Workflows

Documentation classification:

```text
Observe document -> classify role -> compare to canonical blueprints -> edit or archive -> update index/status -> run contradiction scan
```

Implementation change:

```text
Read status -> choose roadmap phase -> inspect current code -> make scoped change -> test -> update status if architecture state changed
```

Project snapshot:

```text
Identify milestone -> create dev_journey/snapshots/YYYY-MM-DD_short-name -> copy only relevant files -> write SNAPSHOT.md and FILE_MANIFEST.md -> update CHANGELOG.md
```

Workspace generation design:

```text
Collect raw input -> clean transcript -> compile prompt -> run gap analysis -> readiness gate -> build workspace -> validate handoff files
```

When uncertain:

- Ask one to three targeted project questions.
- Explain why the answer blocks or changes the build.
- Do not proceed by silently guessing.

## 10. Verification Checklist

Before declaring documentation cleanup complete:

- Root documents explain Amadeus as local Gemma 4 E4B prep agent.
- Root documents do not present Qwen as target model.
- Root documents do not present cloud APIs as required providers.
- Root documents do not present Amadeus as the final task executor.
- `CLAUDE.md` and `AGENTS.md` give clear working instructions.
- `DOCUMENTATION_INDEX.md` maps canonical, status, roadmap, template, research, and legacy files.
- `PROJECT_STATUS.md` separates implemented code from planned architecture.
- Legacy local-AI research is preserved under `docs/research/`.
- Templates for generated target workspaces exist under `docs/templates/`.
- `dev_journey/` contains a current changelog, restore guide, and milestone snapshots.
- A provider/model contradiction scan has been run after edits.
