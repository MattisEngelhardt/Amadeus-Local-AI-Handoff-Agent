# Amadeus Architecture Decisions

Status: Canonical decision log
Date: 2026-05-24

## ADR-001: Amadeus Is A Prep Agent, Not The Final Executor

Decision:

Amadeus prepares AI handoff workspaces. Codex, Claude Code, or Antigravity executes the final project task.

Rationale:

This keeps Gemma 4 E4B focused on structured preparation, gap analysis, prompt compilation, and file orchestration. It avoids overloading a small local model with the full execution task.

Implication:

Any feature that makes Amadeus generate production app files as the final deliverable is legacy or out of scope unless explicitly reframed as workspace preparation.

## ADR-002: Core Model Is `gemma4:e4b`

Decision:

The target core model is Gemma 4 E4B through the Ollama model tag `gemma4:e4b`.

Rationale:

The project direction is local, free after download, and suitable for a guided prep agent with templates, schemas, validators, and readiness gates.

Implication:

Qwen, DeepSeek, Gemini, OpenAI API, Anthropic, Groq, NVIDIA NIM, and OpenRouter are not target model choices for the core workflow.

## ADR-003: Runtime Is Ollama

Decision:

Ollama is the default local runtime.

Rationale:

Ollama gives a practical local model runtime and OpenAI-compatible integration surface without requiring custom llama.cpp compilation as the default.

Implication:

llama.cpp notes are archived as performance research, not current architecture.

## ADR-004: Transcription Is Local `faster-whisper`

Decision:

Voice-to-text is handled by local `faster-whisper`.

Rationale:

The product goal is local, free, and stable transcription without relying on a cloud API key.

Implication:

OpenAI Whisper API may appear only as legacy implementation or optional manually approved fallback, not as core requirement.

## ADR-005: Telegram And Desktop Speechbar Are Primary Inputs

Decision:

Amadeus supports Telegram for mobile/desktop convenience and a local desktop speechbar for fast capture.

Rationale:

Telegram enables easy multi-device input and file transfer. The speechbar enables quick local capture without switching apps.

Implication:

Telegram transport itself is not local, but processing after download remains local.

## ADR-006: Handoff Uses Files

Decision:

Amadeus hands off through a generated workspace on disk.

Rationale:

Files are inspectable, versionable, recoverable, and robust across sessions. Live agent-to-agent control is fragile.

Implication:

The generated workspace must include `CLAUDE.md`, `AGENTS.md`, `MASTER_PROMPT.md`, `SOURCE_MAP.md`, `CONTEXT_INDEX.md`, and supporting folders.

## ADR-007: English Workspace Contract

Decision:

Generated handoff workspaces use English file and folder names.

Rationale:

English names are more stable for Codex, Claude Code, Antigravity, common tooling, and agent conventions.

Implication:

German user input is understood and transformed into English workspace structure where needed.

## ADR-008: Readiness Gate Before Build

Decision:

Amadeus must not build the final workspace while blockers remain unless the user explicitly approves documented assumptions.

Rationale:

The main product value is better preparation. Building too early transfers ambiguity to the executing agent.

Implication:

Gap analysis, blocker tracking, and user approval are core behavior, not optional polish.

## ADR-009: Legacy Research Is Preserved But Non-Canonical

Decision:

Old local-AI and Qwen/llama.cpp research is preserved under `docs/research/`, with full originals under `docs/research/originals/`.

Rationale:

The research contains useful implementation patterns, but it also contains old model/provider decisions that conflict with the current target.

Implication:

Future agents may extract patterns from archive files, but must not treat archived model/provider choices as current architecture.

## ADR-010: Amadeus Keeps A Dev Journey Folder

Decision:

Amadeus keeps its own project history under `dev_journey/`.

Rationale:

The project needs a visible fallback and development-journey layer in addition to Git. This helps future agents understand why the folder changed, where stable milestone states are preserved, and how to restore curated documentation states without guessing.

Implication:

Major documentation, architecture, and implementation milestones should update `dev_journey/CHANGELOG.md` and, when useful, add a snapshot under `dev_journey/snapshots/`.

Snapshots must be curated. They should not become uncontrolled full copies of the repository.
