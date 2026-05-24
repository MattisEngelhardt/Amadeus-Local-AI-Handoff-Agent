# Amadeus Restore Guide

This guide explains how to use `dev_journey/snapshots/` as a fallback mechanism.

## Principle

Snapshots are not automatic full-repository backups. They are curated restore points for important project states.

Before restoring, inspect:

1. `SNAPSHOT.md`
2. `FILE_MANIFEST.md`
3. the copied files in the snapshot
4. current `PROJECT_STATUS.md`

## Manual Restore Workflow

1. Choose a snapshot folder under `dev_journey/snapshots/`.
2. Read its `SNAPSHOT.md`.
3. Compare current files against the snapshot files.
4. Restore only the files needed for the rollback.
5. Update `PROJECT_STATUS.md` and `dev_journey/CHANGELOG.md` to record the rollback.

## Recommended PowerShell Pattern

Use explicit file paths. Do not bulk-copy blindly over the whole repository.

Example:

```powershell
Copy-Item -LiteralPath .\dev_journey\snapshots\2026-05-24_documentation-cleanup\root_docs\CLAUDE.md -Destination .\CLAUDE.md
```

## Restore Warnings

- Do not restore archived legacy research as canonical root documentation.
- Do not overwrite `config.yaml` or code files from a documentation snapshot.
- Do not restore old provider/model assumptions into current canonical docs.
- If a snapshot predates a user decision, ask before restoring it as current truth.
