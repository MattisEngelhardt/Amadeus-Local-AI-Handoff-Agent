# Legacy Qwen And llama.cpp Notes

Status: Archived legacy research, non-canonical
Date: 2026-05-24

These notes preserve technical lessons from earlier Qwen and llama.cpp research. They are not the current Amadeus architecture.

Current Amadeus target:

- Model: `gemma4:e4b`.
- Runtime: Ollama.
- Transcription: local `faster-whisper`.
- Role: prep agent and workspace builder.

Full original source preserved:

- `docs/research/originals/LOCAL_AI_AGENT_MASTERCLASS_ORIGINAL.md`

## Useful Technical Lessons

VRAM sizing:

- Account for model weights plus KV cache.
- Context length increases memory pressure.
- Quantization affects both speed and quality.

Structured output handling:

- Local models may produce wrappers, reasoning tags, or extra prose around JSON.
- Use schema validation and controlled extraction before accepting outputs.
- Prefer template-guided JSON or Markdown code block extraction for structured fields.

Reasoning tag cleanup:

- If a local model emits `<think>`-style traces, strip them before JSON parsing or file writing.
- Log problematic raw output for debugging.
- Never write unvalidated model output directly into generated files.

Validation loops:

- Treat failed parsing as repairable model output, not as accepted state.
- Add retries with stricter prompts.
- Add deterministic validators for required fields.

Operational caution:

- A high-performance local runner is useful only if it remains maintainable.
- Default runtime should stay simple unless measured bottlenecks justify complexity.

## Superseded Technical Direction

Do not use this archive to reintroduce:

- Qwen as Amadeus target model.
- llama.cpp as default runtime.
- DeepSeek-specific reasoning parser assumptions.
- cloud fallback as standard behavior.
- code-generation-first architecture.

## What Can Be Reused

Reusable ideas must be translated into the current Gemma/Ollama architecture:

- schema-first outputs,
- output sanitization,
- validation before file writes,
- source-preserving logs,
- performance-aware model configuration,
- eval cases before fine-tuning.
