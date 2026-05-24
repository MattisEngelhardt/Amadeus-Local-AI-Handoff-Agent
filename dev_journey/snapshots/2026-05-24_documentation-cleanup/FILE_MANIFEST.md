# File Manifest

Snapshot: `2026-05-24_documentation-cleanup`

## Root Docs

Copied to `root_docs/`:

- `CLAUDE.md`
- `AGENTS.md`
- `README.md`
- `PROJECT_STATUS.md`
- `REQUIREMENTS.md`
- `DOCUMENTATION_INDEX.md`
- `IMPLEMENTATION_ROADMAP.md`
- `AMADEUS_WORKFLOW_BLUEPRINT.md`
- `GEMMA_TO_AMADEUS_BLUEPRINT.md`

## Decision Docs

Copied to `docs_decisions/`:

- `ARCHITECTURE_DECISIONS.md`
- `AMADEUS_DOCUMENTATION_CLEANUP_PLAN.md`

## Restore Notes

- Restore root docs only when reverting documentation or project-brain changes.
- Restore decision docs only when the decision log itself was damaged or accidentally overwritten.
- Do not restore this snapshot over implementation files.
- After restoring, update `PROJECT_STATUS.md` and `dev_journey/CHANGELOG.md`.
