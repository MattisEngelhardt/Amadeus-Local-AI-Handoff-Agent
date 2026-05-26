# {{PROJECT_NAME}} Agent Instructions

These instructions are for Codex and other coding agents working in this
Amadeus-generated handoff workspace.

## Project Direction

Goal:

{{PROJECT_GOAL}}

Amadeus prepared this workspace. You are the executing agent: complete the
project task from the prepared context, prompts, decisions, source map, and next
steps. Do not treat Amadeus as having executed the final task already.

Prepared executing agents:

{{EXECUTING_AGENTS}}

## Non-Negotiables

{{CONSTRAINTS}}

## Source of Truth

Read in this order:

1. `CLAUDE.md`
2. `PROJECT_BRIEF.md`
3. `MASTER_PROMPT.md`
4. `REQUIREMENTS.md`
5. `DECISIONS.md`
6. `NEXT_STEPS.md`
7. `CONTEXT_INDEX.md`
8. `SOURCE_MAP.md`

`CLAUDE.md` is the deeper project brain. This file is the concise Codex entry
point.

## File Map

{{FILE_MAP_TABLE}}

## Commands

{{COMMANDS}}

## Context-Reading Rules

- Prefer `_context/` over `_sources/`.
- Verify source coverage in `SOURCE_MAP.md`.
- Use `CONTEXT_INDEX.md` before opening large source material.
- Preserve citations, source IDs, extraction notes, and uncertainty markers.
- Do not invent missing facts, files, constraints, commands, or source coverage.

## Editing Discipline

- Keep changes scoped to `MASTER_PROMPT.md`, `REQUIREMENTS.md`, and
  `NEXT_STEPS.md`.
- Update `DECISIONS.md` before making a scope-affecting change.
- Preserve `_sources/`, `_context/`, `_logs/`, and `_versions/`.
- If blocked, state the exact missing decision, source, command, or user answer.
- Keep generated workspace file and folder names in English.

## Definition of Done

- All requirements are satisfied or explicitly deferred with rationale.
- Non-goals and non-negotiables are respected.
- Source-backed claims remain traceable through `SOURCE_MAP.md`.
- Required verification has passed, or skipped checks are documented with a
  concrete reason.
- Remaining blockers, assumptions, and risks are documented before finishing.

## Implementation Priorities

{{NEXT_STEPS_CONTENT}}
