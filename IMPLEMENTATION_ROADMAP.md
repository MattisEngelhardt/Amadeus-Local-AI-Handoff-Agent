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

## Completion Roadmap After Phase 9

Phase 9 completed the first reliable handoff-workspace core: local Gemma/Ollama
analysis, deterministic state, gap analysis, readiness gating, workspace
generation, `CLAUDE.md`/`AGENTS.md`, source maps, snapshots, and validation
reports.

The remaining roadmap turns that core into the complete Amadeus dream goal:

```text
amadeus
-> always-available local terminal agent
-> Gemma 4 E4B through Ollama
-> local tools for files, voice, documents, images, links, memory, validation
-> perfect AI handoff workspace
-> Codex / Claude Code / Antigravity executes the final user task
```

Important architecture boundary:

- Ollama is the local model runtime and stores the Amadeus model identity,
  parameters, prompt template, and structured-output settings.
- The Amadeus application is the agent control layer. It owns filesystem tools,
  transcription, document conversion, image/OCR handling, project state,
  memory, readiness gates, validators, repair loops, UI channels, and release
  packaging.
- The final product is not just `ollama run amadeus`. It is a local CLI and
  channel agent named `amadeus` that uses Ollama/Gemma as its reasoning core.

Global done means:

- `amadeus` can be launched from any terminal.
- The user can create, resume, inspect, and build projects without remembering
  Python module commands.
- Amadeus can accept text, voice, files, links, screenshots/images, and old
  prompts.
- Amadeus can read/convert supported materials locally, preserve originals,
  write context Markdown, and map every source.
- Amadeus can ask targeted questions and block builds while true blockers
  remain.
- Amadeus can generate a complete handoff workspace that an executing agent can
  use immediately without manual context search.
- All critical behavior is covered by tests, validation reports, smoke builds,
  and end-to-end eval cases.

## Phase 10: Baseline Evaluation Harness

Status: Implemented on 2026-05-28. Versioned eval suite with 14 canonical cases, deterministic runner, and scorecard generation integrated.

Goal: make future quality measurable before expanding the agent surface.

Why this is first:

- Phase 9 gave us validators, but validators only check structural correctness.
- The next phases will add more tools and channels; without eval cases we cannot
  tell whether Amadeus is getting more useful or merely more complex.
- Evaluation must stay local and deterministic enough to run in CI where
  possible, while allowing optional local Gemma smoke evals.

Scope:

- Create a versioned eval suite under `evals/`.
- Cover text-only, voice-derived, material-heavy, missing-context,
  contradiction, and handoff-target scenarios.
- Separate deterministic checks from model-quality scoring.

Tasks:

- Add `evals/cases/` with at least 12 canonical cases:
  - German app idea from rough text.
  - German voice transcript for a coding project.
  - Academic/report project with missing citation style.
  - Project referencing an attached PDF that is absent.
  - Project with one TXT/MD source file.
  - Project with conflicting user statements.
  - Project with an old prompt plus correction.
  - Project where the user explicitly allows assumptions.
  - Codex-only handoff.
  - Claude Code + Codex handoff.
  - Screenshot/image-driven UI project placeholder.
  - Telegram-style multi-message project transcript.
- Add `evals/schema.py` or equivalent Pydantic models for:
  - input payload,
  - expected blockers,
  - expected assumptions,
  - expected materials,
  - expected generated files,
  - expected validation status,
  - scoring notes.
- Add an eval runner command:
  - `python -m amadeus eval --mode deterministic`
  - later `python -m amadeus eval --mode local-model`
- Score at least:
  - requirement extraction,
  - blocker detection,
  - assumption discipline,
  - readiness score reasonableness,
  - source map completeness,
  - prompt section completeness,
  - handoff usability.
- Store eval results under `dev_journey/evals/` or `_eval_runs/` with timestamp,
  command, commit hash, and summary.
- Add regression tests for the deterministic runner.

Acceptance:

- At least 12 eval cases exist and are documented.
- Deterministic eval runner can run without network and without cloud APIs.
- Eval output includes pass/fail plus a numeric quality score per case.
- CI or local verification can detect regressions in gap analysis, source
  mapping, workspace structure, and validator behavior.
- `PROJECT_STATUS.md` records the baseline score before Phase 11 starts.

Verification:

- `python -m pytest tests -q`
- `python -m ruff check .`
- `python -m amadeus eval --mode deterministic`

## Phase 11: Global Terminal Agent CLI

Status: Implemented on 2026-05-28. Added Project Registry and subcommands for new, add, status, gaps, build, validate, projects, use, and open.

Goal: make Amadeus feel like a real local agent in every terminal.

Target UX:

```powershell
amadeus
amadeus new "Build a local REST API from my notes"
amadeus add notes.md
amadeus add screenshot.png
amadeus status
amadeus gaps
amadeus materials
amadeus build
amadeus validate
amadeus open
```

Tasks:

- Add a proper CLI command surface while keeping `python -m amadeus` working.
- Add commands:
  - `amadeus check-runtime`
  - `amadeus new`
  - `amadeus add`
  - `amadeus transcribe`
  - `amadeus status`
  - `amadeus gaps`
  - `amadeus prompt`
  - `amadeus materials`
  - `amadeus build`
  - `amadeus validate`
  - `amadeus open`
  - `amadeus eval`
- Add a local project registry so `amadeus status` can find the active project.
- Add `--project`, `--project-dir`, and `--output-dir` consistently.
- Add an interactive shell mode:
  - shows active project,
  - accepts short commands,
  - displays blockers before build,
  - never hides validation errors.
- Add install guidance for global command availability on Windows:
  - editable install,
  - script shim,
  - PATH guidance.
- Keep CLI output concise, actionable, and German-input friendly while generated
  workspace names remain English.

Acceptance:

- `amadeus` runs from a normal terminal after documented installation.
- All existing build-text behavior remains available.
- A user can create, add material, inspect gaps, build, and validate from CLI
  without touching Python internals.
- Active project selection is deterministic and visible.

Verification:

- CLI unit tests for every command parser path.
- Integration test: create -> add TXT -> status -> build -> validate.
- Manual smoke on Windows PowerShell using the global `amadeus` command.

## Phase 12: Agent Tool Runtime And Mode Orchestrator

Status: Implemented on 2026-05-28. Added Pydantic tool definitions, safe execution wrappers, agent mode states, and dry-run loop via Ollama structured output.

Goal: turn Amadeus from a linear CLI pipeline into a controlled local agent that
can decide which Amadeus tool to run next.

Design principle:

- Gemma proposes structured actions.
- Python executes tools.
- Validators verify the result.
- State records every significant action.

Agent loop:

```text
Observe -> Summarize -> Decide -> Act -> Validate -> Record
```

Tasks:

- Define a local tool registry with typed tool contracts.
- Start with these tools:
  - `create_project`
  - `save_raw_input`
  - `transcribe_audio`
  - `clean_transcript`
  - `ingest_material`
  - `inspect_link`
  - `run_gap_analysis`
  - `render_prompt`
  - `render_readiness`
  - `build_workspace`
  - `run_validation_suite`
  - `write_decision`
  - `create_snapshot`
- Add structured output schemas for tool decisions.
- Add mode prompts and schemas for:
  - Intake Mode,
  - Transcription Review Mode,
  - Prompt Compiler Mode,
  - Gap Analyst Mode,
  - Workspace Architect Mode,
  - Build Orchestrator Mode.
- Add guardrails:
  - no destructive file operations outside configured workspace roots,
  - no build while open blockers remain unless explicitly waived,
  - no cloud LLM provider as a required path,
  - no silent source invention,
  - every tool action logs intent/result.
- Add a dry-run mode that shows proposed tool actions without executing them.

Acceptance:

- Amadeus can run a multi-step local agent loop for one project.
- Tool decisions are parsed through Pydantic models, not free-form text.
- Failed tool calls produce actionable errors and do not corrupt state.
- The old deterministic pipeline can still be used directly by tests.

Verification:

- Unit tests for tool schemas and tool registry.
- Simulated agent-loop tests with mocked Gemma decisions.
- Smoke: text input -> proposed actions -> build workspace.

## Phase 13: Intake Inbox And Project Registry

Status: Implemented on 2026-05-28. Centralized inbox, duplicate detection, and project archive support added.

Goal: make all raw inputs first-class project evidence.

Tasks:

- Add an inbox layer under project state:
  - raw text snippets,
  - audio files,
  - documents,
  - images/screenshots,
  - links,
  - old prompts,
  - user corrections.
- Add stable input IDs and source IDs.
- Store every raw input under `_logs/raw_inputs/` or `_sources/` before
  cleaning/conversion.
- Add duplicate detection by content digest.
- Add project registry fields:
  - active project,
  - last opened project,
  - project root,
  - created/updated timestamps,
  - readiness summary.
- Add commands:
  - `amadeus projects`
  - `amadeus use <project>`
  - `amadeus archive <project>`
- Add conflict handling when two projects have similar names.

Acceptance:

- Every input has provenance before any model analysis runs.
- User can resume a project later and see exactly what Amadeus knows.
- Duplicate materials are detected and recorded, not silently reprocessed.

Verification:

- Tests for input registration, duplicate detection, and registry loading.
- Smoke: create two projects, switch active project, add different materials.

## Phase 14: Complete Local Voice Pipeline

Status: Implemented on 2026-05-28. Full faster-whisper integration, artifact generation, and transcript state integration added.

Goal: make German voice input a reliable local first-class path.

Tasks:

- Implement audio capture normalization:
  - mono,
  - 16 kHz target,
  - stable temp/source file naming,
  - explicit failure messages for missing microphone/audio dependencies.
- Complete faster-whisper integration:
  - `large-v3` default,
  - fallback to configured smaller model,
  - language fixed to German where configured,
  - timestamps where available,
  - uncertainty markers where available.
- Write transcript artifacts:
  - `_logs/transcripts/<timestamp>_raw.md`
  - `_logs/transcripts/<timestamp>_clean.md`
  - transcript metadata in `amadeus_state.json`.
- Add transcript cleanup via local Gemma:
  - filler cleanup,
  - semantic sectioning,
  - unclear terms,
  - possible requirements,
  - possible missing context.
- Add manual correction command:
  - `amadeus transcript edit`
  - records corrected transcript as a new version.

Acceptance:

- A local audio file can be transcribed and added to a project.
- Raw and clean transcripts are preserved separately.
- Clean transcript never overwrites raw transcript.
- Transcript uncertainty becomes either an open question or a recorded note.

Verification:

- Unit tests with a small fixture or mocked faster-whisper.
- Manual smoke with a real German voice note.
- Validation suite catches missing raw/clean transcript files.

## Phase 15: Material Ingestion V2: Documents, Images, OCR, Links

Status: Implemented on 2026-05-28. Added real PDF and DOCX adapters, image metadata extraction, and link ingestion.

Goal: make Amadeus actually able to read the material types the user expects.

Supported source types:

- `.txt`
- `.md`
- `.markdown`
- `.pdf`
- `.docx`
- common image formats: `.png`, `.jpg`, `.jpeg`, `.webp`
- screenshots
- links saved as link records
- old prompt files

Tasks:

- Replace PDF adapter stubs with real local extraction:
  - text extraction,
  - page numbers,
  - extraction notes for tables/images,
  - optional OCR fallback for scanned pages if local OCR is configured.
- Replace DOCX adapter stubs with real extraction:
  - headings,
  - paragraphs,
  - tables,
  - metadata where available.
- Add image ingestion:
  - preserve original under `_sources/`,
  - create `_context/<source-id>.md`,
  - include dimensions, format, OCR text if available,
  - include visual description if a local vision path is available,
  - otherwise mark as image material requiring manual review.
- Add screenshot-specific context:
  - UI text/OCR,
  - visible layout notes,
  - inferred constraints marked as inference.
- Add link ingestion:
  - store URL and purpose,
  - fetch only when explicitly supported and safe,
  - save fetched text under `_context/`,
  - record fetch timestamp and source URL.
- Add extraction confidence fields.
- Add tests for success, partial extraction, unsupported files, corrupt files,
  missing dependencies, and path safety.

Acceptance:

- TXT/MD/PDF/DOCX/images can be registered and source-mapped.
- Broken or partial conversions are visible in extraction notes.
- Original files remain unchanged under `_sources/`.
- The generated workspace tells the executing agent exactly which source
  material is reliable, partial, or needs manual review.

Verification:

- `python -m pytest tests/test_material_ingestion.py tests/test_validation_suite.py -q`
- Smoke with one TXT, one DOCX, one PDF, and one screenshot.

## Phase 16: Source Mapping And Evidence Ledger

Goal: make every claim in the handoff traceable back to raw user input or
material.

Tasks:

- Extend `MaterialRecord` and related models with:
  - source digest,
  - original filename,
  - context filename,
  - source type,
  - extraction status,
  - confidence,
  - page/section anchors where available.
- Add an evidence ledger:
  - raw input evidence,
  - transcript evidence,
  - document evidence,
  - image/OCR evidence,
  - link evidence,
  - user decision evidence.
- Add stable references usable in Markdown:
  - `source:brief-pdf#page-3`
  - `input:voice-2026-05-27`
  - `decision:readiness-waiver`
- Update `SOURCE_MAP.md` to include:
  - original path,
  - converted path,
  - material purpose,
  - reliability/extraction notes,
  - referenced handoff sections.
- Update `CONTEXT_INDEX.md` for quick navigation.
- Update validators to reject broken evidence references.

Acceptance:

- Amadeus can explain why each major requirement exists.
- The executing agent can trace requirements to source material without
  searching the whole workspace.
- Missing evidence is visible as an assumption, not hidden as fact.

Verification:

- Tests for evidence IDs, markdown rendering, and broken references.
- Smoke build with mixed sources and evidence-linked requirements.

## Phase 17: Interactive Readiness Review And Repair Loop

Goal: make blockers actionable instead of just reported.

Tasks:

- Add interactive readiness review:
  - show blockers first,
  - show assumptions second,
  - show optional improvements last,
  - show why each item matters,
  - offer answer, waive, defer, or add material.
- Add CLI commands:
  - `amadeus review`
  - `amadeus answer <gap-id>`
  - `amadeus waive <gap-id> --reason "..."`
  - `amadeus defer <gap-id>`
- Add repair actions:
  - missing file -> prompt user to add file,
  - missing target environment -> ask one precise question,
  - unsupported material -> ask for supported replacement,
  - partial extraction -> mark manual review or ask user to confirm.
- Update project state after each answer.
- Re-run gap analysis and readiness score after every meaningful change.

Acceptance:

- User can resolve blockers without editing JSON or Markdown manually.
- Every waiver is recorded in `DECISIONS.md` with rationale.
- Build remains blocked until blockers are resolved or explicitly waived.

Verification:

- Tests for answer/waive/defer state transitions.
- Smoke: intentionally blocked project -> answer blocker -> build succeeds.

## Phase 18: Skills, Constitution, And Mode Files

Goal: make Amadeus' behavior portable, inspectable, and reusable.

Tasks:

- Add canonical skills under repository-controlled templates:
  - prompt-writing skill,
  - CLAUDE.md writing skill,
  - AGENTS.md writing skill,
  - workspace-building skill,
  - gap-analysis skill,
  - source-mapping skill,
  - proactive-questioning skill,
  - academic-source-prep skill,
  - versioning-and-fallback skill,
  - image/screenshot-source-prep skill.
- Add an Agent Constitution file that captures non-negotiable rules.
- Add mode prompt files for the six Amadeus modes.
- Add a skill selector:
  - choose skills based on project type,
  - include selected skills in `_skills/`,
  - reference them from `CLAUDE.md` and `AGENTS.md`.
- Add tests that generated workspaces include the expected skills for target
  scenarios.

Acceptance:

- Amadeus does not rely only on one giant system prompt.
- Skills are versioned, inspectable, and included only when relevant.
- Generated handoff workspaces teach the executing agent the right local rules.

Verification:

- Skill selection unit tests.
- Generated workspace tests for skill inclusion and cross-links.

## Phase 19: Handoff Workspace V2

Goal: make the generated workspace feel production-grade for Codex, Claude Code,
and Antigravity.

Tasks:

- Improve `MASTER_PROMPT.md`:
  - evidence-linked requirements,
  - explicit ambiguity section,
  - task-specific execution plan,
  - target-agent-specific notes.
- Improve `CLAUDE.md`:
  - state machine fields,
  - exact first-read sequence,
  - source-reading policy,
  - evidence citation policy,
  - verification strategy,
  - quality rubric tied to user task.
- Improve `AGENTS.md`:
  - concise Codex-compatible execution rules,
  - command placeholders,
  - expected test strategy,
  - explicit relation to `CLAUDE.md`.
- Improve `NEXT_STEPS.md`:
  - not generic,
  - derived from project type,
  - references blockers/assumptions.
- Add target-specific handoff variants when useful:
  - Codex first,
  - Claude Code first,
  - Antigravity first,
  - multi-agent.
- Add post-build self-review:
  - run validation suite,
  - generate quality summary,
  - create final snapshot.

Acceptance:

- A fresh executing agent can start from the workspace without asking "what is
  this project?".
- Workspace files are not merely present; they contain task-specific,
  source-grounded, execution-ready instructions.
- Generated instructions remain honest about missing context.

Verification:

- Golden-file tests for representative generated workspaces.
- Human review of at least 5 handoff outputs.
- Eval score improves over Phase 10 baseline.

## Phase 20: Telegram Channel

Goal: make Telegram the primary mobile/desktop input channel.

Tasks:

- Add Telegram bot configuration without making Telegram a model provider.
- Support commands:
  - `/new`
  - `/status`
  - `/gaps`
  - `/materials`
  - `/prompt`
  - `/build`
  - `/cancel`
  - `/reset`
- Support Telegram text messages.
- Support Telegram voice messages:
  - download voice file,
  - convert if needed,
  - transcribe locally,
  - save raw and clean transcripts.
- Support Telegram documents:
  - download files,
  - preserve originals,
  - ingest supported material types.
- Add user/project routing:
  - one active project per user by default,
  - explicit project switching.
- Add safety:
  - file size limits,
  - allowed extensions,
  - clear errors for unsupported types,
  - no hidden cloud LLM calls.

Acceptance:

- A user can start a project from Telegram voice and build a handoff workspace.
- Telegram files are processed locally after download.
- Telegram commands reflect the same state as the CLI.

Verification:

- Unit tests with mocked Telegram updates.
- Manual Telegram smoke: `/new` -> voice -> file -> `/gaps` -> `/build`.

## Phase 21: Desktop Speechbar Productionization

Goal: make quick local voice capture ergonomic and reliable.

Tasks:

- Verify global hotkey behavior on Windows.
- Make recording state visible and unambiguous.
- Allow transcript review before submission.
- Add project selection or quick-create flow.
- Route accepted transcript into the same intake/state pipeline as CLI and
  Telegram.
- Add clear failure states:
  - microphone unavailable,
  - transcription failed,
  - Ollama unavailable,
  - active project missing.
- Add logs for support/debugging without leaking unnecessary user content.

Acceptance:

- User can press the hotkey, speak German, review text, submit to Amadeus, and
  see project state updated.
- Speechbar does not bypass readiness or validation.
- Desktop and CLI see the same project state.

Verification:

- UI smoke on Windows.
- Mocked tests for recording/transcription routing.

## Phase 22: Memory System

Goal: let Amadeus improve continuity without overriding current user facts.

Memory layers:

- user preference memory,
- project memory,
- skill memory,
- reflection memory.

Tasks:

- Add local memory storage with clear file locations.
- Add memory scopes:
  - global user preferences,
  - per-project facts,
  - reusable skill notes,
  - reviewed reflections.
- Add memory precedence:
  - current user input wins,
  - current project decisions win,
  - memory can suggest but not silently override.
- Add commands:
  - `amadeus memory list`
  - `amadeus memory add`
  - `amadeus memory forget`
  - `amadeus memory review`
- Add reflection capture after failed evals or corrected outputs.
- Add memory injection into analyzer/gap/prompt modes with size limits.

Acceptance:

- Amadeus remembers stable preferences like "German input, English workspace".
- Amadeus does not treat old memory as source truth for a new project.
- Reflections can improve future behavior through explicit rules before any
  fine-tuning exists.

Verification:

- Tests for memory precedence and deletion.
- Smoke: create two projects with conflicting preferences; current project wins.

## Phase 23: Validation Repair Autopilot

Goal: validators should trigger repair or targeted questions, not just reports.

Tasks:

- Map validation issues to repair actions:
  - missing file -> regenerate file,
  - missing section -> repair file section,
  - broken source reference -> update source map or mark missing material,
  - empty raw input -> ask user or mark input missing,
  - open blocker while handoff_ready -> revert phase or block build.
- Add `amadeus repair` command.
- Add pre-build and post-build repair passes with limits:
  - no infinite loops,
  - every repair logged,
  - user approval required for semantic scope changes.
- Add repair result reports:
  - fixed,
  - needs user input,
  - cannot fix automatically.

Acceptance:

- Common structural validation failures can be repaired automatically.
- Semantic failures become targeted questions.
- A workspace never appears "ready" while validation errors remain unresolved
  unless explicitly documented as waived where allowed.

Verification:

- Tests for each repair mapping.
- Smoke: intentionally delete generated file -> repair -> validate clean.

## Phase 24: Full Evaluation And Learning Loop

Goal: continuously improve Amadeus quality with real examples before any
fine-tuning.

Tasks:

- Expand eval suite from Phase 10 to at least 25 cases.
- Add scenario classes:
  - app build handoff,
  - research/report handoff,
  - UI/screenshot handoff,
  - multi-file handoff,
  - missing context handoff,
  - Telegram voice handoff,
  - desktop speechbar handoff.
- Add rubric scoring:
  - source faithfulness,
  - blocker discipline,
  - prompt quality,
  - workspace navigability,
  - generated `CLAUDE.md` usefulness,
  - generated `AGENTS.md` usefulness,
  - readiness decision correctness.
- Add accepted/corrected example capture.
- Add reflection generation after reviewed failures.
- Add trend reports by commit.

Acceptance:

- Regressions are visible before releases.
- Improvements are tied to measured eval changes.
- Fine-tuning remains blocked until curated examples exist.

Verification:

- `python -m amadeus eval --mode deterministic`
- optional local-model eval against `amadeus`
- release gate includes eval summary.

## Phase 25: Packaging, Installer, And Runtime Doctor

Goal: make Amadeus installable and maintainable on the user's machine.

Tasks:

- Add package metadata for CLI entry point.
- Add Windows install script or documented install flow.
- Add `amadeus doctor`:
  - Python version,
  - Ollama reachable,
  - `gemma4:e4b` present,
  - `amadeus` model present,
  - faster-whisper import/model availability,
  - OCR/PDF/DOCX optional dependency status,
  - writable workspace/output dirs,
  - PATH/global command status.
- Add `amadeus setup`:
  - verify Ollama,
  - show missing commands,
  - create/update `amadeus` Ollama model from `Modelfile`.
- Add release checklist.

Acceptance:

- A fresh checkout can be turned into a working local Amadeus install through
  documented commands.
- Runtime problems are diagnosed by `amadeus doctor` with clear next actions.

Verification:

- Clean-environment setup test where possible.
- Manual Windows install smoke.

## Phase 26: Reliability, Privacy, And Safety Hardening

Goal: make Amadeus safe enough for real personal/project material.

Tasks:

- Define workspace root safety rules.
- Harden path handling for all file operations.
- Add file size and type limits.
- Add redaction controls for logs where appropriate.
- Ensure raw inputs are preserved but not accidentally published in releases.
- Add backup/restore commands:
  - `amadeus snapshot`
  - `amadeus restore`
  - `amadeus export`
- Add failure recovery:
  - interrupted build,
  - partial material ingestion,
  - invalid state JSON,
  - missing model,
  - unavailable microphone.
- Add privacy documentation:
  - what stays local,
  - what Telegram sends through Telegram servers,
  - what is never sent to cloud LLMs in core path.

Acceptance:

- Amadeus avoids unsafe path writes.
- User can recover from interrupted or bad project states.
- Privacy boundaries are explicit and test-covered where possible.

Verification:

- Path safety tests.
- Corrupt-state recovery tests.
- Backup/restore smoke.

## Phase 27: Dream Goal End-to-End Acceptance

Goal: prove that Amadeus fully embodies the blueprints.

Required end-to-end scenarios:

- CLI text-only project:
  - `amadeus new`
  - build workspace,
  - validation clean.
- CLI mixed-material project:
  - add TXT/MD/PDF/DOCX/image,
  - source map complete,
  - readiness review clean or explicitly waived.
- German voice project:
  - record or ingest audio,
  - raw and clean transcripts preserved,
  - workspace generated.
- Telegram voice + file project:
  - project created,
  - voice transcribed locally after download,
  - file ingested,
  - blockers reviewed,
  - workspace built.
- Desktop speechbar project:
  - hotkey capture,
  - transcript review,
  - build from same state store.
- Missing-material project:
  - build blocked,
  - targeted question generated,
  - user resolves blocker,
  - build succeeds.
- Executing-agent handoff:
  - Codex or Claude Code opens generated workspace,
  - starts from `CLAUDE.md`/`AGENTS.md`,
  - no manual context search required.

Acceptance:

- All end-to-end scenarios pass on the target Windows machine.
- All generated workspaces include complete logs, source maps, context indices,
  snapshots, and validation reports.
- Amadeus remains local-first: no cloud LLM provider is required.
- The final release has a clear version tag, GitHub release, changelog, and
  restore snapshot.

Verification:

- Full test suite.
- Full eval suite.
- Manual end-to-end smoke matrix.
- Release checklist signed off in `PROJECT_STATUS.md`.

## Phase 28: Optional Fine-Tuning Decision Gate

Goal: decide whether LoRA/QLoRA/DPO is justified by evidence.

This phase is optional and must not start until Phases 10-27 provide enough
curated data.

Tasks:

- Review accepted/corrected examples.
- Identify repeated model-only weaknesses that cannot be solved cleanly by:
  - prompts,
  - tools,
  - validators,
  - repair loops,
  - skills,
  - memory.
- Build a small supervised dataset only from reviewed examples.
- Run a baseline-vs-adapter eval.
- Keep `gemma4:e4b` as the fixed base model.
- Use an adapter only if evals show measurable improvement and no regression in
  source faithfulness or blocker discipline.

Acceptance:

- Fine-tuning is either rejected with evidence or accepted with measured gains.
- No adapter becomes required unless it improves the full eval suite.
- The non-fine-tuned local Amadeus path remains usable.

Verification:

- Baseline eval report.
- Adapter eval report if tested.
- Explicit architecture decision record before adoption.
