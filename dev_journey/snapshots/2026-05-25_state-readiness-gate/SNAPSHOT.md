# Snapshot: Project State And Readiness Gate

Date: 2026-05-25
Purpose: fallback marker for the first Amadeus version with persistent project
state, deterministic gap analysis, and a pre-build readiness gate.

## What Changed

- Added `amadeus/models/state.py` with the project state contract.
- Added `_logs/amadeus_state.json`, `_logs/gap_analysis.json`, and
  `_logs/readiness_gate.md` as generated state artifacts.
- Added deterministic gap analysis and readiness scoring.
- Added readiness-gate enforcement before workspace build.
- Added documented waiver support for builds with open blockers.
- Centralized CLI and desktop speechbar handoff preparation in `core/workflow.py`.
- Updated generated handoff files to reflect state, blockers, assumptions, and
  readiness notes.
- Added regression tests for allowed, blocked, and approved readiness flows.

## Verified

```powershell
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-smoke --project-name readiness-smoke-handoff --text "Build a CLI tool workspace that summarizes study notes into a report and includes verification steps."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-block --project-name readiness-block-handoff --text "Build a report from the attached PDF file and preserve citations."
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-readiness-approved --project-name readiness-approved-handoff --text "Build a report from the attached PDF file and preserve citations." --approve-readiness --approval-note "Proceed with a text-only handoff now; the missing PDF is documented as a waived blocker."
```

## Smoke Artifacts

- Allowed build:
  `C:\tmp\amadeus-readiness-smoke\readiness-smoke-handoff`
- Blocked review package:
  `C:\tmp\amadeus-readiness-block\readiness-block-handoff`
- Approved build:
  `C:\tmp\amadeus-readiness-approved\readiness-approved-handoff`

Generated smoke workspaces are intentionally not committed.

## Restore Notes

Restore from the matching GitHub commit or release tag after this snapshot is
pushed. Runtime assets remain outside Git:

- Ollama installation.
- `gemma4:e4b` and `amadeus` model store entries.
- `faster-whisper-large-v3` Hugging Face cache.

Recreate runtime assets on a fresh machine:

```powershell
winget install --id Ollama.Ollama -e --source winget
ollama pull gemma4:e4b
ollama create amadeus -f amadeus/Modelfile
.\.venv\Scripts\python.exe -m pip install -r amadeus/requirements.txt
.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-large-v3')"
.\.venv\Scripts\python.exe -m amadeus check-runtime
```
