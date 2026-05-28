# Codex 4 — Phase 6 Integration + Phase 7 Workspace Builder

## Prompt für den nächsten Agent

Kopiere diesen Block und sende ihn als Nachricht:

```
@CODEX_4_PLAN.md enthält den vollständigen, genehmigten Implementierungsplan für Phase 6 Integration + Phase 7 Workspace Builder. Setze diesen Plan jetzt Schritt für Schritt um.

Wichtig:
- Folge der Implementierungsreihenfolge (Schritt 1–12) exakt wie im Plan beschrieben.
- Die drei Spike-Dateien liegen im Worktree unter C:\tmp\amadeus-material-ingestion — kopiere sie als erstes nach main.
- Führe nach jedem Schritt die relevanten Tests aus.
- Am Ende: pytest amadeus/tests -q, ruff check amadeus, und den Smoke-Test aus Teil 5 Schritt 11.
- Committe NICHT automatisch — ich sage dir wann.
```

---

## Context

Amadeus ist ein lokal laufender Gemma-4-E4B-Prep-Agent, der rohe Sprache, Texte und Dateien in vollständige KI-Handoff-Workspaces für Codex, Claude Code und Antigravity verwandelt.

**Was bereits erledigt ist (Codex 1–3):**

| Codex | Phase | Ergebnis |
|-------|-------|----------|
| Codex 1 | Phase 0–2 (Identity, Ollama/Gemma, Transcription) | Amadeus läuft lokal mit Gemma über Ollama, CLI, `check-runtime`, `build-text` |
| Codex 2 | Phase 3–5 (State, Prompt Compiler, Gap Analysis) | Persistenter State (`_logs/amadeus_state.json`), Gap Analysis, Readiness Gate, Build blockt bei Blockern, `--approve-readiness` Flag |
| Codex 3 | Phase 6 Spike (Material Ingestion) | Isolierter Spike in Worktree `C:\tmp\amadeus-material-ingestion` — 3 Dateien, 10 Tests, **NICHT committed, NICHT auf main** |

**Aktueller Stand:** Wir sind bei Phase 7 (Workspace Builder). Phase 6 (Material Processing) hat einen funktionierenden Spike, der aber noch nicht in `main` integriert ist. Der Workspace Builder existiert teilweise (generiert alle 9 kanonischen Dateien), aber ohne echte Material-Integration, Source-Mapping, Versioning oder Skill-Delegation.

**Warum dieser Plan nötig ist:** Phase 7 kann nicht sauber fertiggestellt werden, ohne Phase 6 vorher zu integrieren — der Workspace Builder muss Materialien verarbeiten, in `_sources/` und `_context/` ablegen, und `SOURCE_MAP.md` / `CONTEXT_INDEX.md` mit echten Daten füllen. Deshalb ist dieser Plan ein **kombinierter Phase 6 Integration + Phase 7 Enhancement Plan**.

---

## Teil 1: Phase 6 Integration — Material Ingestion in main bringen

### 1.1 Spike-Dateien von Worktree nach main kopieren

Die drei Spike-Dateien liegen als uncommitted working-tree changes in `C:\tmp\amadeus-material-ingestion`:

| Quelle (Worktree) | Ziel (main) |
|---|---|
| `C:\tmp\amadeus-material-ingestion\amadeus\core\material_ingestion.py` | `amadeus/core/material_ingestion.py` |
| `C:\tmp\amadeus-material-ingestion\amadeus\tests\test_material_ingestion.py` | `amadeus/tests/test_material_ingestion.py` |
| `C:\tmp\amadeus-material-ingestion\amadeus\docs\decisions\MATERIAL_INGESTION_NOTES.md` | `amadeus/docs/decisions/MATERIAL_INGESTION_NOTES.md` |

**Aktion:** Dateien 1:1 kopieren, keine inhaltlichen Änderungen am Spike-Code in diesem Schritt.

### 1.2 Material Ingestion in den Workflow einbauen

Laut `MATERIAL_INGESTION_NOTES.md` und den Blueprints muss die Ingestion **VOR** der Gap Analysis laufen, damit fehlgeschlagene Extraktionen als explizite Blocker erscheinen.

**Datei: `amadeus/core/workflow.py`** — `prepare_handoff_workspace()` erweitern:

Aktueller Flow:
```
1. StateStore.create_for_text()     → ProjectState
2. GapAnalyzer.analyze()            → GapAnalysisResult
3. GapAnalyzer.apply_to_state()     → state updated
4. ReadinessGate check/approve
5. Generator.generate_all_files()
6. Scaffolder.scaffold()
```

Neuer Flow:
```
1. StateStore.create_for_text()     → ProjectState
2. ★ MaterialIngestion (NEU)        → materials[] in state gefüllt
3. GapAnalyzer.analyze()            → GapAnalysisResult (jetzt mit Material-Kontext)
4. GapAnalyzer.apply_to_state()     → state updated
5. ReadinessGate check/approve
6. Generator.generate_all_files()   → jetzt mit echten Material-Daten
7. Scaffolder.scaffold()            → kopiert auch _sources/ und _context/
```

**Konkrete Änderungen an `workflow.py`:**

```python
# Nach Schritt 1 (create_for_text), vor Schritt 2 (gap analysis):

def _ingest_materials(state: ProjectState, source_files: list[Path]) -> ProjectState:
    """Ingest all provided source files into _sources/ and _context/."""
    from amadeus.core.material_ingestion import ingest_material

    context_dir = Path(state.target_path) / "_context"
    sources_dir = Path(state.target_path) / "_sources"
    context_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    for source_path in source_files:
        # 1. Original in _sources/ kopieren
        dest = sources_dir / source_path.name
        shutil.copy2(source_path, dest)

        # 2. Konvertieren nach _context/
        result = ingest_material(source_path, context_dir)

        # 3. MaterialRecord im State registrieren
        record = MaterialRecord(
            source_id=result.source_id,
            original_path=f"_sources/{source_path.name}",
            context_path=result.context_path or "",
            material_type=source_path.suffix.lstrip("."),
            purpose="User-provided material",
            status="converted" if result.status == "ingested" else "failed",
            extraction_notes=list(result.extraction_notes),
        )
        state.materials.append(record)

    return state
```

**Neue CLI-Parameter für `build-text`:**

In `amadeus/__main__.py` beim `build-text` Subparser:
```python
build_parser.add_argument("--materials", nargs="*", default=[], help="Source files to ingest")
```

### 1.3 Gap Analysis mit Material-Kontext erweitern

**Datei: `amadeus/core/gap_analysis.py`** — `GapAnalyzer.analyze()` anpassen:

- Wenn `state.materials` nicht leer ist UND alle `status == "converted"`: kein Material-Blocker
- Wenn `state.materials` Material mit `status == "failed"` enthält: Blocker mit spezifischer Fehlermeldung
- Wenn Text auf Materialien verweist aber `state.materials` leer ist: Blocker (wie bisher)
- Wenn Materialien vorhanden aber Text keine Materialien referenziert: Optional-Item ("Unreferenced materials attached")

### 1.4 Tests für die Integration

**Neue Tests in `amadeus/tests/test_readiness_workflow.py`:**

1. `test_workflow_with_text_material_ingests_and_builds` — `.txt`-Datei wird als Material übergeben, erscheint in `SOURCE_MAP.md` und `CONTEXT_INDEX.md`
2. `test_workflow_with_failed_material_creates_blocker` — Nicht-existierende Datei erzeugt Blocker
3. `test_workflow_with_unsupported_material_creates_blocker` — `.zip`-Datei erzeugt Blocker

---

## Teil 2: Phase 7 — Workspace Builder vollständig machen

### 2.1 SOURCE_MAP.md und CONTEXT_INDEX.md mit echten Daten füllen

**Datei: `amadeus/core/generator.py`** — `generate_all_files()` anpassen:

**SOURCE_MAP.md** (aus `state.materials`):
```markdown
# Source Map

| Source ID | Original | Converted | Purpose | Status |
|-----------|----------|-----------|---------|--------|
| source-001 | _sources/methodology.pdf | _context/source-001-methodology.md | Academic reference | converted |
```

**CONTEXT_INDEX.md** (aus `state.materials` + `state.links`):
```markdown
# Context Index

## Materials
| # | Context File | Type | Purpose | Extraction Notes |
|---|-------------|------|---------|-----------------|
| 1 | _context/source-001-methodology.md | pdf | Academic reference | Pages 14-18 may need review |

## Links
| # | URL | Purpose | Status |
|---|-----|---------|--------|
```

### 2.2 _sources/ und _context/ als echte Verzeichnisse befüllen

**Datei: `amadeus/core/scaffolder.py`** — `scaffold()` erweitern:

1. Originale aus `state.materials[].original_path` nach `project_root/_sources/` kopieren (falls noch nicht dort)
2. README.md in `_sources/` und `_context/` mit Inventar aktualisieren

**Wichtig:** Die eigentliche Datei-Konvertierung passiert in Schritt 1.2 (Material Ingestion im Workflow). Der Scaffolder stellt nur sicher, dass alles am richtigen Platz ist.

### 2.3 _skills/ Delegation implementieren

1. **Neues Feld in `WorkspacePlan`** (`amadeus/models/state.py`):
   ```python
   skills_to_include: list[str] = []
   ```

2. **Skill-Resolver im Generator** (`amadeus/core/generator.py`):
   - Wenn `state.workspace_plan.skills_to_include` nicht leer, kopiere Skill-Dateien nach `_skills/`
   - Default: minimales `_skills/README.md`

3. **Scope:** Infrastruktur vorbereiten, Skill-Inhalte sind Phase 8.

### 2.4 _versions/ Snapshot-Mechanismus implementieren

**Neue Datei: `amadeus/core/versioning.py`**

```python
def create_workspace_snapshot(
    project_path: Path,
    reason: str,
    files_to_snapshot: list[str] | None = None,
) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    snapshot_dir = project_path / "_versions" / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    target_files = files_to_snapshot or [
        "CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md",
        "PROJECT_BRIEF.md", "REQUIREMENTS.md", "DECISIONS.md",
    ]

    for fname in target_files:
        src = project_path / fname
        if src.exists():
            shutil.copy2(src, snapshot_dir / fname)

    (snapshot_dir / "SNAPSHOT.md").write_text(
        f"# Snapshot {timestamp}\n\nReason: {reason}\n"
    )
    return snapshot_dir
```

**Integration:** `workflow.py` erstellt nach erfolgreichem Build einen initialen Snapshot.

### 2.5 _logs/ vollständig machen

Fehlend: `_logs/build_log.md` — Protokoll des Build-Prozesses.

**Neue Generierung im Generator:**
```python
def _generate_build_log(state, gap_analysis, readiness_report) -> str:
    # Build-Zeitpunkt, Phase-Übergänge, Material-Verarbeitung,
    # Gap-Analysis-Zusammenfassung, Readiness-Ergebnis, generierte Dateien
```

### 2.6 Workspace-Validierung nach dem Build

**Neue Datei: `amadeus/core/workspace_validator.py`**

```python
def validate_workspace(project_path: Path) -> list[str]:
    errors = []
    # 1. Alle 9 kanonischen Dateien vorhanden?
    # 2. Alle 5 kanonischen Verzeichnisse vorhanden?
    # 3. CLAUDE.md nicht leer?
    # 4. SOURCE_MAP.md referenziert existierende Dateien?
    # 5. Keine deutschen Datei-/Ordnernamen?
    return errors
```

**Integration:** `workflow.py` ruft nach `scaffold()` auf. Warnungen loggen, Build nicht abbrechen.

---

## Teil 3: Blueprint-Alignment

### AMADEUS_WORKFLOW_BLUEPRINT.md

| Anforderung | Status nach Plan |
|---|---|
| §12 Originale in `_sources/`, konvertiert in `_context/` | ✅ |
| §12 Extraktionsprobleme dokumentieren | ✅ `extraction_notes` |
| §14 Standardstruktur | ✅ |
| §15 Alle 9 Dateien | ✅ |
| §16 CLAUDE.md 10 Pflichtsäulen | ✅ Template |
| §17 Versionierung | ✅ `versioning.py` |
| §13 Readiness Gate | ✅ |

### GEMMA_TO_AMADEUS_BLUEPRINT.md

| Anforderung | Status nach Plan |
|---|---|
| §7.5 Workspace Architect Mode | ✅ Echte Daten |
| §7.6 Build Orchestrator Mode | ✅ Workflow + Validator |
| §8 Skills Infrastruktur | ✅ Vorbereitet |
| §9 Tool Rituals | ✅ Pipeline |
| §10.3 Workspace Plan Schema | ✅ |
| §12 Validation | ✅ `workspace_validator` |

---

## Teil 4: Datei-für-Datei Änderungsplan

### Neue Dateien

| Datei | Zweck |
|---|---|
| `amadeus/core/material_ingestion.py` | Vom Spike — Material-Konvertierung |
| `amadeus/core/versioning.py` | Workspace-Snapshot-Mechanismus |
| `amadeus/core/workspace_validator.py` | Post-Build-Validierung |
| `amadeus/tests/test_material_ingestion.py` | Vom Spike — 10 Tests |
| `amadeus/tests/test_versioning.py` | Snapshot-Tests |
| `amadeus/tests/test_workspace_validator.py` | Validator-Tests |
| `amadeus/docs/decisions/MATERIAL_INGESTION_NOTES.md` | Vom Spike — Design-Notizen |

### Zu ändernde Dateien

| Datei | Änderung |
|---|---|
| `amadeus/core/workflow.py` | Material Ingestion + Versioning + Validation einbauen |
| `amadeus/core/gap_analysis.py` | Material-Status-Check (failed → Blocker) |
| `amadeus/core/generator.py` | SOURCE_MAP/CONTEXT_INDEX mit Daten, Build-Log, Skills-README |
| `amadeus/core/scaffolder.py` | _sources/ Kopie |
| `amadeus/models/state.py` | `WorkspacePlan.skills_to_include` |
| `amadeus/__main__.py` | `--materials` Parameter |
| `amadeus/tests/test_readiness_workflow.py` | 3 neue Integrationstests |

### Nicht geänderte Dateien

`ollama_client.py`, `analyzer.py`, `readiness.py`, `recorder.py`, `transcriber.py`, `validator.py`, `models/project.py`, `models/requirements.py`, `main.py`

---

## Teil 5: Implementierungsreihenfolge

### Schritt 1: Spike-Dateien übernehmen
1. `material_ingestion.py` von Worktree nach `amadeus/core/`
2. `test_material_ingestion.py` von Worktree nach `amadeus/tests/`
3. `MATERIAL_INGESTION_NOTES.md` von Worktree nach `amadeus/docs/decisions/`
4. `pytest amadeus/tests/test_material_ingestion.py -q` → 10 passed
5. `pytest amadeus/tests -q` → alle Tests grün

### Schritt 2: State-Model erweitern
1. `WorkspacePlan.skills_to_include: list[str] = []` in `amadeus/models/state.py`

### Schritt 3: Workflow-Integration
1. `_ingest_materials()` in `workflow.py` einfügen
2. `prepare_handoff_workspace()` um `source_files` Parameter erweitern
3. Material Ingestion vor Gap Analysis

### Schritt 4: Gap Analysis erweitern
1. Material-Status-Check: `status == "failed"` → Blocker

### Schritt 5: Generator erweitern
1. `SOURCE_MAP.md` mit echten Material-Daten
2. `CONTEXT_INDEX.md` mit echten Material-Daten
3. `_logs/build_log.md` generieren
4. `_skills/README.md` erweitern

### Schritt 6: Scaffolder erweitern
1. Originaldateien nach `_sources/` kopieren

### Schritt 7: Versioning implementieren
1. `versioning.py` — `create_workspace_snapshot()`
2. `workflow.py` — Snapshot nach Build

### Schritt 8: Workspace-Validator implementieren
1. `workspace_validator.py` — `validate_workspace()`
2. `workflow.py` — Validierung nach Scaffold

### Schritt 9: CLI erweitern
1. `__main__.py` — `--materials` Parameter

### Schritt 10: Tests schreiben und ausführen
1. `test_versioning.py`
2. `test_workspace_validator.py`
3. `test_readiness_workflow.py` — 3 neue Tests
4. `pytest amadeus/tests -q`
5. `ruff check amadeus`

### Schritt 11: Smoke-Test
```bash
# 1. Regression ohne Materials
python -m amadeus build-text --text "Build me a REST API for task management" --output-dir C:\tmp\amadeus-smoke-phase7

# 2. Build mit Material
echo "Important project notes" > C:\tmp\test-material.txt
python -m amadeus build-text --text "Build me a REST API, see attached notes" --materials C:\tmp\test-material.txt --output-dir C:\tmp\amadeus-smoke-phase7-materials

# Verifizieren:
# - _sources/ enthält test-material.txt
# - _context/ enthält konvertierte .md
# - SOURCE_MAP.md enthält Eintrag
# - CONTEXT_INDEX.md enthält Eintrag
# - _versions/ enthält initialen Snapshot
# - _logs/build_log.md existiert
```

### Schritt 12: Dev-Journey-Snapshot und Dokumentation
1. `dev_journey/snapshots/2026-05-26_workspace-builder-materials/SNAPSHOT.md`
2. `dev_journey/CHANGELOG.md` aktualisieren
3. `PROJECT_STATUS.md` aktualisieren
4. `IMPLEMENTATION_ROADMAP.md` — Phase 6+7 Status-Marker

---

## Teil 6: Definition of Done

### Tests
- [ ] `pytest amadeus/tests -q` — alle Tests grün (~26 Tests)
- [ ] `ruff check amadeus .github pyproject.toml` — clean
- [ ] `python -m amadeus check-runtime` — Ollama ok

### Funktional
- [ ] `build-text` ohne `--materials` funktioniert (Regression)
- [ ] `build-text` mit `--materials` erzeugt echte SOURCE_MAP.md und CONTEXT_INDEX.md
- [ ] Fehlende Materialien erzeugen Blocker
- [ ] `_sources/` enthält Original
- [ ] `_context/` enthält Markdown
- [ ] `_versions/` enthält Snapshot
- [ ] `_logs/build_log.md` existiert
- [ ] Workspace-Validator läuft clean

### Blueprint-Compliance
- [ ] Struktur entspricht AMADEUS_WORKFLOW_BLUEPRINT.md §14
- [ ] Alle 9 Dateien (§15)
- [ ] Originale in `_sources/` (§12)
- [ ] Konvertierte in `_context/` (§12)
- [ ] Englische Namen (§14)
- [ ] Readiness Gate (§13)
- [ ] Snapshots (§17)

---

## Bewusst ausgeklammert

| Thema | Wann stattdessen |
|---|---|
| Echte PDF/DOCX-Extraktion | Separater PR |
| Skill-Dateien schreiben | Phase 8 |
| Telegram-Integration | Nach Phase 8 |
| Desktop-Speechbar Material-Upload | Spätere Phase |
| Evaluation Suite | Phase 9+ |
