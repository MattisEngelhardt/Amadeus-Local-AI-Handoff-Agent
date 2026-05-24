# Local AI Research Archive

Status: Archived research, non-canonical
Date: 2026-05-24

This document preserves useful lessons from earlier local-AI planning without allowing old provider/model decisions to override the current Amadeus architecture.

Canonical direction remains:

- `gemma4:e4b` via Ollama.
- Local `faster-whisper`.
- No required cloud LLM provider.
- Amadeus prepares handoff workspaces; it does not execute the final user task.

Full original source preserved:

- `docs/research/originals/LOCAL_AI_PLAN_ORIGINAL.md`
- `docs/research/originals/LOCAL_LLM_AGENT_SETUP_ORIGINAL.md`

## Useful Patterns To Keep

Local-first architecture:

- Prefer local processing for sensitive project context.
- Treat cloud paths as optional manual review/export paths only when explicitly requested.
- Keep local runtime configuration simple and reproducible.

Ollama integration:

- Use an OpenAI-compatible local endpoint where practical.
- Target `http://localhost:11434/v1` for local model calls after implementation refactor.
- Keep model identity stable through config and system prompts.

Hardware awareness:

- Plan model size around available VRAM and realistic context needs.
- Avoid runtime choices that require complex manual compilation unless performance data justifies it.
- Prefer operational reliability over theoretical maximum throughput.

Structured agent outputs:

- Use schemas for prompt sections, gap analysis, workspace plans, and validation results.
- Validate required fields before accepting model output.
- Store machine-readable state separately from prose summaries.

Observability:

- Log model calls, validation failures, conversion warnings, and readiness decisions.
- Preserve raw input and cleaned output separately.
- Keep decision records searchable.

Prompt and workspace templates:

- Do not rely on Gemma to invent perfect file structures from scratch.
- Render stable templates for `CLAUDE.md`, `AGENTS.md`, `SOURCE_MAP.md`, `CONTEXT_INDEX.md`, and `NEXT_STEPS.md`.

## Superseded Ideas

The following ideas are archived only and must not return as current architecture without explicit user approval:

- Hybrid local/cloud provider switching as the normal workflow.
- NVIDIA NIM, Groq, OpenRouter, Anthropic, Gemini, or OpenAI API as core LLM providers.
- Qwen as the target model.
- llama.cpp as the default runtime.
- Project code generation as the primary Amadeus output.
- Cloud fallback as a silent automatic path.

## Integrated Gemma/Ollama Notes

The root-level setup note selected Gemma 4 E4B and Ollama as the practical local direction. That part matches the current target.

Keep:

- Gemma 4 E4B as local model target.
- Ollama as operational runtime.
- Local inference as cost-stable, privacy-preserving backbone.

Discard or archive:

- NVIDIA NIM as automatic fallback.
- Provider-agnostic switchboard as default architecture.
- Groq/OpenRouter as current options.

## Implementation Lessons For Later

When implementation reaches local model calls:

- Build one local LLM client abstraction.
- Add explicit model/runtime health checks.
- Store model config in one place.
- Add structured-output retry and validation.
- Never let failed local output silently become accepted context.
