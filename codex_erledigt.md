# Was von Codex bereits erledigt wurde

---

## Codex 1 – Amadeus läuft lokal mit Gemma über Ollama

**Erledigt:** Amadeus läuft jetzt lokal mit Gemma über Ollama und der Stand ist auf GitHub gesichert.

### Umgesetzt

- Ollama 0.24.0 installiert.
- `gemma4:e4b` lokal heruntergeladen.
- Lokales Amadeus-Modell `amadeus` / `amadeus:latest` aus `amadeus/Modelfile` erstellt.
- `faster-whisper-large-v3` lokal in den Hugging-Face-Cache geladen.
- Amadeus-Code auf `amadeus.*` refaktoriert, lokaler Ollama-Client ergänzt, CLI ergänzt.
- `python -m amadeus build-text ...` erzeugt jetzt echte Handoff-Workspaces.
- Dev-Journey Snapshot angelegt: `amadeus/dev_journey/snapshots/2026-05-24_local-gemma-runtime/SNAPSHOT.md`
- GitHub Push erledigt: commit `2e10bfe` _Make Amadeus run locally with Gemma_ auf `origin/main`.

### Verifiziert

```
.\.venv\Scripts\python.exe -m amadeus check-runtime
.\.venv\Scripts\python.exe -m pytest amadeus/tests study_agent/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
.\.venv\Scripts\python.exe -m amadeus build-text --output-dir C:\tmp\amadeus-smoke --project-name amadeus-smoke-handoff --text "..."
```

Alle Checks waren grün. Smoke-Workspace liegt bei: `C:\tmp\amadeus-smoke\amadeus-smoke-handoff`

> **Hinweis:** Das Gesamtziel ist noch nicht vollständig abgeschlossen. Der lokale Gemma-Kern läuft jetzt, aber für den „fertigen voll funktionsfähigen" Amadeus fehlen noch Projekt-State, echte Gap-Analysis/Readiness-Gate, Material-Ingestion, Telegram und Live-Test der Desktop-Speechbar.

---

## Codex 2 – Phase 3-5 Kern ist fertig und veröffentlicht

**Erledigt.** Schrittstand: **Phase 3-5 Kern ist fertig und veröffentlicht.**

### Umgesetzt

- Persistenter Project State: `_logs/amadeus_state.json`
- Gap Analysis: `_logs/gap_analysis.json`
- Readiness Gate: `_logs/readiness_gate.md`
- Build blockt jetzt bei echten Blockern, z.B. fehlendes PDF.
- Build kann mit dokumentierter Freigabe laufen: `--approve-readiness --approval-note "..."`
- CLI und Desktop-Speechbar-Pipeline nutzen denselben Workflow.
- Journey-Snapshot angelegt: `amadeus/dev_journey/snapshots/2026-05-25_state-readiness-gate/`

### Verifiziert

- `pytest amadeus/tests study_agent/tests -q`: 8 passed
- `ruff check amadeus .github pyproject.toml`: passed
- `git diff --cached --check`: passed
- `python -m amadeus check-runtime`: Ollama, gemma4:e4b, amadeus ok
- CLI-Smokes:
  - normaler Readiness-Build ok
  - fehlendes PDF blockt korrekt
  - fehlendes PDF mit Waiver baut korrekt

### GitHub

- Commit auf `main` gepusht: `10adf8c` _Add Amadeus project state readiness gate_
- Tag gepusht: `amadeus-v0.1.0`
- GitHub Release erstellt: https://github.com/MattisEngelhardt/My-AI-Agents/releases/tag/amadeus-v0.1.0
- Amadeus-Download-ZIP hochgeladen: https://github.com/MattisEngelhardt/My-AI-Agents/releases/download/amadeus-v0.1.0/amadeus-v0.1.0.zip

Arbeitsbaum ist sauber bis auf das bereits vorhandene untracked `codex 1.png`, das bewusst nicht angefasst wurde.

> **Nächster sinnvoller Schritt:** **Phase 6 Material-Ingestion** integrieren, danach Desktop-Speechbar live testen und Telegram anbinden.

---

## Codex 3 – Material-Ingestion Spike im isolierten Worktree

**Erledigt** im isolierten Worktree: `C:\tmp\amadeus-material-ingestion` auf Branch `codex/material-ingestion-spike`.

### Umgesetzt

- `amadeus/core/material_ingestion.py` (Z. 41): isolierter Converter-Kern mit `MaterialIngestionResult`, `ingest_material(...)`, Text/Markdown-Ingestion, PDF/DOCX-Adapter-Stubs und klaren Statuswerten.
- `amadeus/tests/test_material_ingestion.py` (Z. 9): 10 lokale Tests ohne Ollama und ohne Netzwerk.
- `amadeus/docs/decisions/MATERIAL_INGESTION_NOTES.md` (Z. 40): Findings, Verifikation, Diff Summary und Integrationsnotiz für den nächsten Codex.

### Verifiziert

- `pytest amadeus/tests/test_material_ingestion.py -q` → 10 passed
- `pytest amadeus/tests -q` → 18 passed
- `ruff check amadeus .github pyproject.toml` → passed
- `git diff --check` → passed, nur Git-CRLF-Warnungen

### Diff

- 3 neue Dateien
- 474 Insertions
- keine verbotenen Core-/State-/Readiness-/Workflow-Dateien geändert
- kein Commit, kein Push, `main` nicht verändert

> **Hinweis:** Die ältere volle Testzeile mit `study_agent/tests` ist in diesem Worktree nicht ausführbar, weil `study_agent/tests` dort nicht existiert; das ist in der Handoff-Notiz festgehalten.

Goal abgeschlossen: 74.654 Tokens, ca. 10 Minuten. Kein zweites Goal gestartet, da die nächste sinnvolle Aufgabe die Core-Integration wäre und damit bewusst den zuvor gesperrten Dateiscope öffnet. Die konkrete empfohlene nächste Aufgabe steht in `MATERIAL_INGESTION_NOTES.md`.
