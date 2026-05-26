# File Manifest

Snapshot: `2026-05-26_phase8-claude-agents-generation`

## Snapshot Files

| Path | Purpose |
|---|---|
| `SNAPSHOT.md` | Snapshot summary, verification notes, and restore context. |
| `FILE_MANIFEST.md` | This manifest. |
| `docs/templates/TARGET_CLAUDE_TEMPLATE.md` | Phase 8 generated `CLAUDE.md` template. |
| `docs/templates/TARGET_AGENTS_TEMPLATE.md` | Phase 8 generated `AGENTS.md` template. |
| `core/generator.py` | Rich target-template context injection and generated workspace files. |
| `core/workspace_validator.py` | Workspace validation plus `CLAUDE.md` and `AGENTS.md` anatomy validators. |
| `core/gap_analysis.py` | Supporting material-reference heuristic fix used by the Phase 8 smoke build. |
| `tests/test_generator_handoff_files.py` | Generated handoff file quality tests. |
| `tests/test_workspace_validator.py` | Anatomy validator tests. |
| `tests/test_readiness_workflow.py` | Readiness workflow regression test for future CSV input files. |
| `amadeus/__init__.py` | Package path shim for `amadeus.*` imports from this repository root. |
| `root_docs/IMPLEMENTATION_ROADMAP.md` | Roadmap status after Phase 8. |
| `root_docs/PROJECT_STATUS.md` | Project status after Phase 8. |
| `dev_journey/CHANGELOG.md` | Changelog with the Phase 8 milestone entry. |
