# Amadeus Dev Journey

This folder records the development journey of Amadeus itself.

It exists for two reasons:

1. Preserve fallback snapshots before or after major changes.
2. Show how the project evolved over time, including architecture decisions, cleanup phases, implementation phases, and important reversibility points.

This is not a replacement for Git. It is a human- and agent-readable project memory layer that makes the path of the project easy to understand even when working outside a clean commit history.

## Folder Contract

```text
dev_journey/
|-- README.md
|-- CHANGELOG.md
|-- RESTORE_GUIDE.md
`-- snapshots/
    `-- YYYY-MM-DD_short-name/
        |-- SNAPSHOT.md
        |-- FILE_MANIFEST.md
        |-- root_docs/
        `-- docs_decisions/
```

## What Belongs Here

Use this folder for:

- documentation cleanup snapshots,
- architecture decision checkpoints,
- pre-refactor and post-refactor snapshots,
- implementation milestone summaries,
- restore instructions,
- files needed to reconstruct a known good project state.

Do not use this folder for:

- random backups,
- generated runtime logs,
- dependency caches,
- model downloads,
- large source archives,
- every minor edit.

## Snapshot Rules

Create a new snapshot when:

- canonical architecture changes,
- `CLAUDE.md` or `AGENTS.md` changes substantially,
- `REQUIREMENTS.md` or `IMPLEMENTATION_ROADMAP.md` changes substantially,
- a major implementation phase starts or ends,
- runtime configuration changes from legacy to target architecture,
- a risky refactor begins,
- the user explicitly asks for a fallback point.

Each snapshot must include:

- `SNAPSHOT.md`: why the snapshot exists and what changed,
- `FILE_MANIFEST.md`: copied files and restore notes,
- copied files grouped by role.

## Current Snapshots

- `snapshots/2026-05-24_local-gemma-runtime/`: first working local Ollama/Gemma runtime and handoff workspace smoke test.
- `snapshots/2026-05-24_documentation-cleanup/`: first clean Amadeus documentation workspace after canonicalization around Gemma/Ollama/faster-whisper.
