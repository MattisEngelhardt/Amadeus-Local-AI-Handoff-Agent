# Amadeus Implementation Roadmap

Status: Canonical build plan
Date: 2026-05-24

This roadmap translates the canonical blueprints into implementation phases.

## Phase 0: Repository Alignment

Goal: make the codebase match the Amadeus identity before adding new behavior.

Tasks:

- Decide whether to rename the package from `speech_to_code` to `amadeus` or provide a stable compatibility package.
- Replace user-facing "Speech to Code" naming with Amadeus.
- Keep imports and tests passing during the transition.
- Update prototype tests to reflect renamed modules.

Acceptance:

- App starts under Amadeus identity.
- Tests can import modules without external junction hacks.
- No product docs describe the old identity as current.

## Phase 1: Ollama/Gemma Harness

Goal: run `gemma4:e4b` locally through a stable client layer.

Tasks:

- Add a local Ollama client abstraction.
- Add Amadeus Modelfile or system identity prompt for `amadeus:local`.
- Implement timeout, retry, logging, and structured response handling.
- Replace Claude/Gemini analysis calls with local Gemma calls.

Acceptance:

- A local prompt can be sent to `gemma4:e4b`.
- Model output is captured, logged, and validated.
- No cloud provider is required for core analysis.

## Phase 2: Local Transcription

Goal: make local `faster-whisper` the default transcription path.

Tasks:

- Update config target after code supports it.
- Prefer `large-v3` when hardware allows.
- Add model-size fallback behavior.
- Preserve raw transcript and cleaned transcript separately.
- Mark uncertain terms.

Acceptance:

- Audio can be transcribed without API keys.
- Raw and clean transcript files are written.
- OpenAI Whisper API is not part of the core path.

## Phase 3: Project State Store

Status: implemented as the first persistent state milestone on 2026-05-25.

Goal: persist project continuity.

Tasks:

- Define project state schema.
- Store raw inputs, transcripts, materials, links, decisions, assumptions, open questions, prompt versions, workspace plan, and readiness score.
- Add phase transitions: `context_collection`, `readiness_review`, `workspace_build`, `handoff_ready`.

Acceptance:

- State survives restart through `_logs/amadeus_state.json`.
- Raw text/audio inputs, transcript metadata, decisions, gaps, prompt versions,
  workspace plan, phase, and readiness are represented in schema.
- Build cannot start from an incomplete state without recorded user approval in
  the shared workflow.

## Phase 4: Prompt Compiler

Goal: generate a professional master prompt from cleaned context.

Tasks:

- Implement prompt section schema.
- Use templates for required sections.
- Version each master prompt.
- Preserve open questions instead of hiding them.

Acceptance:

- `MASTER_PROMPT.md` can be generated.
- Prompt includes all required sections.
- Prompt references source and context files by stable paths.

## Phase 5: Gap Analysis

Status: initial deterministic gap analysis and readiness scoring implemented on 2026-05-25.

Goal: identify blockers before workspace build.

Tasks:

- Implement gap analysis schema.
- Categorize blockers, assumptions, optional improvements, and missing materials.
- Add readiness scoring.
- Generate targeted user questions.

Acceptance:

- Build is blocked when open blockers exist.
- User-approved waivers are recorded as decisions and reflected in generated
  handoff files.
- Gap output is machine-validated through Pydantic and stored as
  `_logs/gap_analysis.json`.

## Phase 6: Material Processing

Status: Implemented basic conversion (.txt, .md) and integrated into workflow on 2026-05-26. PDF/DOCX remain stubs.

Goal: convert user materials into AI-usable context.

Tasks:

- Store originals under `_sources/`.
- Convert PDF, DOCX, TXT, and Markdown to `_context/`.
- Add metadata, extraction notes, and source IDs.
- Create `SOURCE_MAP.md` and `CONTEXT_INDEX.md`.

Acceptance:

- Original files are never overwritten.
- Converted files are traceable.
- Broken conversions are reported.

## Phase 7: Workspace Builder

Status: Implemented completely on 2026-05-26. Creates canonical folders, workspace files, source maps, context indices, and versions.

Goal: build the final handoff workspace.

Tasks:

- Generate required folder tree.
- Generate `PROJECT_BRIEF.md`, `REQUIREMENTS.md`, `DECISIONS.md`, `NEXT_STEPS.md`.
- Copy or render `_skills/` when relevant.
- Add `_versions/` snapshots for major changes.
- Add `_logs/` transcripts and processing notes.

Acceptance:

- Workspace matches the canonical target contract.
- English file/folder names are enforced.
- Build only starts after readiness gate.

## Phase 8: `CLAUDE.md` And `AGENTS.md` Generation

Status: Implemented on 2026-05-26. Templates rewritten with 10-pillar CLAUDE.md and full AGENTS.md anatomy. Validators added.

Goal: create excellent handoff instructions for executing agents.

Tasks:

- Implement templates from `docs/templates/`.
- Generate semantic file maps and quicklinks.
- Add tool/source-reading rules.
- Add quality rubrics and verification checklists.
- Validate anatomy before final handoff.

Acceptance:

- Generated `CLAUDE.md` can orient Claude Code immediately.
- Generated `AGENTS.md` can orient Codex immediately.
- Both files reference the same project state and source map.

## Phase 9: Validation Suite

Status: Implemented on 2026-05-27. Validation suite with 7 validators
(transcript, prompt, gap analysis, material coverage, source map, workspace
tree, handoff anatomy) integrated into the build pipeline.

Goal: prevent weak or incomplete workspaces.

Tasks:

- Add transcript validator.
- Add prompt validator.
- Add gap analysis validator.
- Add material coverage validator.
- Add source map validator.
- Add workspace tree validator.
- Add `CLAUDE.md` and `AGENTS.md` validators.

Acceptance:

- Invalid workspace validation fails with actionable errors in logs and reports.
- Validators can be run in tests.

## Phase 10: Evaluation And Learning Loop

Goal: improve Amadeus without premature fine-tuning.

Tasks:

- Create 10-20 realistic evaluation cases.
- Score gap analysis, prompt quality, source mapping, and handoff readiness.
- Save accepted and corrected examples.
- Add reflection memory entries for repeated failures.
- Consider LoRA/QLoRA/DPO only after high-quality data exists.

Acceptance:

- Baseline eval results exist.
- Regressions are visible.
- Fine-tuning is data-driven, not speculative.
