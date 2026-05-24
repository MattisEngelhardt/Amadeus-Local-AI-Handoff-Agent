# File Manifest

This snapshot is a milestone marker. The authoritative fallback is the Git commit
and GitHub release tag created after this snapshot.

## New Core Files

- `amadeus/models/state.py`
- `amadeus/core/gap_analysis.py`
- `amadeus/core/readiness.py`
- `amadeus/core/state_store.py`
- `amadeus/core/workflow.py`

## Updated Core Files

- `amadeus/__main__.py`
- `amadeus/main.py`
- `amadeus/core/generator.py`

## Tests

- `amadeus/tests/test_readiness_workflow.py`

## Updated Documentation

- `amadeus/PROJECT_STATUS.md`
- `amadeus/IMPLEMENTATION_ROADMAP.md`
- `amadeus/dev_journey/README.md`
- `amadeus/dev_journey/CHANGELOG.md`

## Generated Runtime Artifacts

The workflow now writes these files inside generated handoff workspaces:

- `_logs/amadeus_state.json`
- `_logs/gap_analysis.json`
- `_logs/readiness_gate.md`
- `_logs/raw_input.md`

Smoke workspace paths:

```text
C:\tmp\amadeus-readiness-smoke\readiness-smoke-handoff
C:\tmp\amadeus-readiness-block\readiness-block-handoff
C:\tmp\amadeus-readiness-approved\readiness-approved-handoff
```

The generated smoke workspaces are intentionally not committed.
