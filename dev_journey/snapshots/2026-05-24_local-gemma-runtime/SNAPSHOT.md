# Snapshot: Local Gemma Runtime

Date: 2026-05-24
Purpose: fallback marker for the first locally working Amadeus runtime milestone.

## What Changed

- Ollama was installed on the laptop.
- `gemma4:e4b` was pulled locally.
- `amadeus/Modelfile` was added.
- `amadeus` / `amadeus:latest` was created as the working local model alias.
- `amadeus:local` was tested but is not the target runtime tag on this machine.
- `python -m amadeus check-runtime` verifies Ollama, the base model, and the
  Amadeus model.
- The Python package now imports through `amadeus.*`.
- Local Gemma handles structured input analysis through `core/ollama_client.py`
  and `core/analyzer.py`.
- The generator now creates handoff workspaces rather than production app code.
- Local `faster-whisper` is the transcription default.
- `faster-whisper-large-v3` was preloaded into the local Hugging Face cache.

## Verified

```powershell
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-smoke --project-name amadeus-smoke-handoff --text "..."
```

## Restore Notes

Restore from GitHub after the matching commit is pushed. Runtime assets are not
stored in Git:

- Ollama install lives under the user's Windows app data/program install.
- `gemma4:e4b` and `amadeus` live in Ollama's model store.
- `faster-whisper-large-v3` lives in the Hugging Face cache.

Recreate runtime assets on a fresh machine:

```powershell
winget install --id Ollama.Ollama -e --source winget
ollama pull gemma4:e4b
ollama create amadeus -f amadeus/Modelfile
.\.venv\Scripts\python.exe -m pip install -r amadeus/requirements.txt
.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-large-v3')"
```
