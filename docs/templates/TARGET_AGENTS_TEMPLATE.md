# {{PROJECT_NAME}} Agent Instructions

These instructions are for Codex and other generic coding agents working in this generated handoff workspace.

## Start Here

Read:

1. `MASTER_PROMPT.md`
2. `PROJECT_BRIEF.md`
3. `REQUIREMENTS.md`
4. `NEXT_STEPS.md`
5. `CONTEXT_INDEX.md`
6. `SOURCE_MAP.md`

If you are Claude Code or a Claude-compatible agent, also read `CLAUDE.md` first.

## Project Goal

{{PROJECT_GOAL}}

## Constraints

{{CONSTRAINTS}}

## File Map

- `_sources/`: original user-provided materials. Do not modify.
- `_context/`: converted Markdown context for agent use.
- `_skills/`: optional specialist instructions.
- `_versions/`: snapshots and fallback versions.
- `_logs/`: transcripts, warnings, and processing notes.
- `SOURCE_MAP.md`: provenance and usage map.
- `CONTEXT_INDEX.md`: context navigation.
- `DECISIONS.md`: decisions, assumptions, and rationale.
- `NEXT_STEPS.md`: ordered execution plan.

## Work Rules

- Execute `NEXT_STEPS.md` from top to bottom.
- Use `_context/` before opening originals in `_sources/`.
- Do not invent missing requirements or sources.
- If blocked, state the exact missing decision or material.
- Keep edits scoped to the requested task.
- Preserve generated context and logs.

## Commands

{{COMMANDS}}

## Verification

Before finishing:

- run the listed tests or checks,
- confirm requirements are satisfied,
- confirm non-goals were respected,
- document any remaining risk or blocker.
