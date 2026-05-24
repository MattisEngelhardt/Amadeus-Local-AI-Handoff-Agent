# Snapshot: 2026-05-24 Documentation Cleanup

Status: fallback snapshot
Scope: Amadeus documentation and architecture decisions
Created: 2026-05-24

## Purpose

This snapshot preserves the first clean Amadeus documentation state after the repository was reorganized around the current target architecture.

It is a fallback point for the project brain and documentation map before the implementation refactor begins.

## Canonical Architecture At This Snapshot

- Amadeus is a local Gemma 4 E4B prep agent.
- Core model: `gemma4:e4b`.
- Runtime: Ollama.
- Transcription: local `faster-whisper`.
- Inputs: Telegram and desktop speechbar.
- Output: English-named handoff workspace.
- Handoff targets: Codex, Claude Code, Antigravity.
- Amadeus prepares context, prompts, source maps, decisions, and workspace files.
- Amadeus does not execute the final user task.
- Cloud LLM providers are not required core architecture.

## Snapshot Contents

- `root_docs/`: root-level canonical and status Markdown documents.
- `docs_decisions/`: decision documents that explain the cleanup and architecture choices.

## What This Snapshot Does Not Cover

- Python implementation.
- `config.yaml`.
- `requirements.txt`.
- Runtime templates under `templates/`.
- Legacy research originals.
- Model files or external dependencies.

## Restore Guidance

Use this snapshot to restore project documentation and decision state only. Do not use it as a code rollback.
