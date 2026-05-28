# Amadeus Workflow Blueprint

Stand: 2026-05-24
Status: Kanonischer Zielentwurf vor der Bereinigung der alten Dokumente

Dieses Dokument speichert den finalen Ziel-Workflow fuer Amadeus. Es ist noch keine Implementierungsbeschreibung des vorhandenen Codes, sondern die verbindliche Produkt- und Architektur-Vorgabe fuer den naechsten Build-Schritt.

## 1. Grunddefinition

Amadeus ist ein lokal laufender Gemma-4-E4B-Agent fuer perfekte KI-Vorarbeit.

Amadeus nimmt rohe Sprache, Texte, Dateien und Links entgegen, transkribiert und strukturiert sie, erkennt fehlenden Kontext, fragt proaktiv nach und erstellt am Ende einen vollstaendigen, englisch benannten KI-Handoff-Workspace fuer Codex, Claude Code oder Antigravity.

Amadeus ist nicht der Agent, der die Hauptaufgabe ausfuehrt. Amadeus bereitet alles so vor, dass der ausfuehrende Agent danach ohne manuelles Prompting, ohne Kontextsuche und ohne unscharfe Aufgabenstellung arbeiten kann.

Kurzform:

```text
User
-> Telegram chat / desktop speechbar
-> Amadeus (Gemma 4 E4B + local tools)
-> transcription, cleanup, gap analysis, source processing
-> perfect handoff workspace
-> Codex / Claude Code / Antigravity executes the real task
```

## 2. Nicht verhandelbare Entscheidungen

- Kernmodell: `gemma4:e4b`.
- Runtime: lokal ueber Ollama.
- Kein Qwen, kein DeepSeek, kein Gemini, kein Google-API-Provider, kein NVIDIA NIM, kein Anthropic- oder Groq-Pflichtpfad.
- Amadeus ist Gemma 4 E4B mit Tools, Memory, Skills, Validatoren und Dateisystemzugriff.
- Der Workspace-Contract ist Englisch, auch wenn der User Deutsch spricht.
- Amadeus erstellt keine produktiven App-Dateien als Hauptaufgabe.
- Amadeus erstellt Spezifikationen, Prompts, Kontextdateien, Projektplaene, Agent-Regeln und Versionierungsstrukturen.
- Die Hauptaufgabe wird spaeter von Codex, Claude Code oder Antigravity im vorbereiteten Workspace ausgefuehrt.
- Der Handoff erfolgt ueber Dateien, nicht ueber eine fragile Live-Kommunikation zwischen Gemma und Codex/Antigravity.

## 3. Rollenmodell

### 3.1 User

Der User liefert Anforderungen, Voice-Nachrichten, Dateien, Links, Praeferenzen, Beispiele und Antworten auf Rueckfragen.

### 3.2 Amadeus

Amadeus ist die lokale Agentenidentitaet auf Basis von Gemma 4 E4B. Er:

- versteht und strukturiert Nutzereingaben,
- erkennt Zusammenhaenge,
- hinterfragt unklare Anforderungen,
- fragt proaktiv nach,
- schreibt professionelle Prompts,
- entwirft `CLAUDE.md` / `AGENTS.md`,
- entscheidet, ob die Kontextphase abgeschlossen ist,
- orchestriert Tools fuer Transkription, Dokumentkonvertierung und Workspace-Erstellung.

### 3.3 Tools

Tools sind die Arme und Sinne von Amadeus. Sie tun deterministische Arbeit:

- Telegram-Dateien herunterladen,
- Audio in ein geeignetes Format bringen,
- lokal transkribieren,
- PDF/DOCX/TXT/MD nach Markdown konvertieren,
- Dateien speichern,
- Ordner erzeugen,
- Snapshots schreiben,
- Validierungen ausfuehren.

### 3.4 Codex, Claude Code, Antigravity

Diese Agents sind die spaeteren Ausfuehrer. Sie lesen den von Amadeus erzeugten Workspace und arbeiten die Hauptaufgabe ab.

## 4. Eingangswege

### 4.1 Telegram Chat

Telegram ist der primaere mobile und desktopfaehige Kommunikationskanal.

Unterstuetzte Inputs:

- Voice messages,
- Text messages,
- PDFs,
- DOCX-Dateien,
- Markdown-Dateien,
- Textdateien,
- Links,
- spaeter optional Bilder oder Screenshots.

Wichtige technische Einordnung:

- Telegram selbst ist nicht lokal, weil Nachrichten und Dateien ueber Telegram-Server laufen.
- Die Verarbeitung nach dem Download laeuft lokal auf dem Rechner des Users.
- Telegram ist Komfort- und Eingabeschicht, nicht LLM-Provider.

Moegliche Bot-Kommandos:

```text
/new        start a new Amadeus project
/status     show current project state
/gaps       show missing context and open questions
/materials  list received materials
/prompt     show current master prompt draft
/build      create the final workspace
/cancel     cancel current action
/reset      reset current project state
```

### 4.2 Desktop Speechbar

Die Desktop Speechbar ist der lokale Shortcut-Eingang fuer schnelle Spracheingaben.

Zielverhalten:

- `Ctrl+Space` startet oder stoppt die Aufnahme.
- Die Speechbar erscheint minimal und fokussiert.
- `Enter` sendet den transkribierten Text direkt an Amadeus.
- `Esc` bricht ab.
- Der Text kann vor dem Absenden manuell korrigiert werden.

Diese Funktion ist wichtig, weil sie den Telegram-Workflow auf dem Desktop ergaenzt und schnelle Ideen ohne App-Wechsel erlaubt.

## 5. Projektzustand

Jedes Amadeus-Projekt besitzt einen lokalen Zustand. Dieser Zustand ist die Basis fuer Kontinuitaet, Rueckfragen, Versionierung und den finalen Build.

Minimaler State:

```json
{
  "project_id": "string",
  "project_name": "string",
  "created_at": "datetime",
  "phase": "context_collection | readiness_review | workspace_build | handoff_ready",
  "raw_inputs": [],
  "transcripts": [],
  "materials": [],
  "links": [],
  "decisions": [],
  "assumptions": [],
  "open_questions": [],
  "prompt_versions": [],
  "workspace_plan": null,
  "workspace_path": null,
  "readiness_score": 0
}
```

Die Phasen sind verbindlich:

```text
context_collection -> readiness_review -> workspace_build -> handoff_ready
```

Amadeus darf die Arbeitsphase nicht starten, solange Blocker offen sind.

## 6. Voice-to-Text

### 6.1 Ziel

Telegram-Voice und Desktop-Audio sollen kostenlos und lokal in sehr guten deutschen Text umgewandelt werden.

### 6.2 Standard-Transcriber

Standard:

- `faster-whisper`
- bevorzugtes Modell: `large-v3`, falls Performance auf der Maschine reicht
- Performance-Alternative: `distil-large-v3`
- Sprache bei deutschen Nachrichten festsetzen: `language="de"`

### 6.3 Ehrliche Qualitaetsgrenze

Kostenlos, lokal und "perfekt 1:1 fehlerfrei" ist nicht garantierbar. Amadeus muss deshalb:

- das Rohtranskript unveraendert speichern,
- eine bereinigte Arbeitsfassung separat speichern,
- unsichere Stellen markieren,
- bei kritischen Unklarheiten nachfragen,
- Fachbegriffe und Projektnamen ueber eine projektspezifische Wortliste verbessern.

### 6.4 Transkript-Dateien

Jede Voice-Nachricht erzeugt mindestens:

```text
_logs/transcripts/YYYY-MM-DD_HHMMSS_raw.md
_logs/transcripts/YYYY-MM-DD_HHMMSS_clean.md
```

`raw.md` ist moeglichst wortnah.
`clean.md` ist geglaettet, strukturiert und fuer die Prompt-Synthese vorbereitet.

## 7. Transcript Cleanup

Amadeus nutzt Gemma 4 E4B fuer die semantische Bereinigung, nicht fuer die akustische Transkription.

Ziel der Bereinigung:

- Fuellwoerter entfernen,
- lange gesprochene Gedankenschlangen in klare Saetze trennen,
- Abschnitte bilden,
- Satzzeichen und Struktur ergaenzen,
- Bedeutung erhalten,
- nichts hinzuerfinden,
- Unsicherheiten markieren.

Ausgabeformat:

```md
### Clean Transcript

...

### Unclear Terms

- ...

### Potential Requirements

- ...

### Potential Missing Context

- ...
```

## 8. Prompt Compiler

Amadeus kompiliert aus dem bereinigten Input einen professionellen Aufgabenprompt.

Dieser Prompt ist nicht nur ein schoener Text. Er ist die zentrale Aufgabenbasis fuer den spaeteren ausfuehrenden Agenten.

Pflichtstruktur:

```md
### Context
### Role
### Goal
### Requirements
### Non-Goals
### Working Materials
### Output Expectations
### Working Method
### Step-by-Step Plan
### Quality Criteria
### Risks
### Open Questions
```

Wichtige Regeln:

- Der Prompt muss aus der User-Absicht entstehen, nicht aus erfundenen Annahmen.
- Unklare Punkte kommen in `Open Questions`.
- Fehlende Dateien kommen in `Working Materials` oder `Open Questions`.
- Der Prompt wird versioniert.
- Der Prompt muss in spaeteren Workspace-Dateien wiedergefunden werden.

Pfad:

```text
MASTER_PROMPT.md
_versions/prompts/YYYY-MM-DD_HHMMSS_MASTER_PROMPT.md
```

## 9. Gap Analysis

Die Gap Analysis ist eine Kernfaehigkeit von Amadeus.

Amadeus prueft:

- Ist die Hauptaufgabe eindeutig?
- Ist die Zielumgebung klar?
- Sind alle erwaehnten Materialien vorhanden?
- Sind Quellen, Referenzen oder Beispiele vollstaendig?
- Gibt es harte Verbote?
- Gibt es Formatvorgaben?
- Gibt es Bewertungsrubriken?
- Gibt es Fristen, Zielgruppen, Tonalitaet oder Style Guides?
- Gibt es vorhandene Skills, die eingebunden werden muessen?
- Gibt es Widersprueche zwischen Voice-Input, Dateien und alten Prompts?

Kategorien:

```text
Blocker       must be answered before build
Assumption    can proceed only if explicitly recorded
Optional      useful but not required
```

Beispiel-Ausgabe:

```json
{
  "blockers": [
    {
      "question": "Which citation style should the writing agent use?",
      "why_it_matters": "The generated CLAUDE.md must constrain citations before the writing task starts.",
      "expected_answer_type": "short_text"
    }
  ],
  "assumptions": [],
  "optional_improvements": [],
  "readiness_score": 72
}
```

## 10. Proactive Questioning Loop

Amadeus darf nicht still raten, wenn Kontext fehlt. Er fragt aktiv nach.

Regeln:

- Eine Frage muss begruendet sein.
- Mehrere Fragen sollen gruppiert werden.
- Blocker-Fragen haben Vorrang.
- Nach jeder Antwort aktualisiert Amadeus den Projektzustand.
- Der User kann explizit erlauben, mit markierten Annahmen weiterzumachen.

Beispiel:

```text
I can build the workspace, but two blockers remain:

1. Which execution environment should the final handoff target first: Codex, Claude Code, or both?
2. You mentioned scientific sources, but only two PDFs are attached. Are more sources required?
```

## 11. Material Collection

Amadeus sammelt alle Materialien, die der User ueber Telegram oder Desktop bereitstellt.

Materialtypen:

- PDF,
- DOCX,
- Markdown,
- TXT,
- Links,
- alte Prompts,
- Skills,
- Beispiele,
- spaeter optional Bilder/Screenshots.

Speicherregel:

```text
_sources/   original files, unchanged
_context/   AI-optimized Markdown versions
```

Originale duerfen nicht ueberschrieben werden.

## 12. Document Processing

Ziel: Jede Datei wird fuer spaetere KI-Arbeit in strukturiertes Markdown uebersetzt.

Pflichten:

- Originaldatei in `_sources/` speichern.
- Markdown-Version in `_context/` erzeugen.
- Titel, Quelle, Ursprungspfad und Verwendungszweck angeben.
- Relevante Seiten-/Abschnittsverweise erhalten, soweit extrahierbar.
- Extraktionsprobleme offen dokumentieren.
- Keine unlesbaren oder kaputten Konvertierungen still akzeptieren.

Beispiel fuer eine Kontextdatei:

```md
# Source: doering-methodology.pdf

Source ID: `source-003`
Original file: `_sources/doering-methodology.pdf`
Converted file: `_context/source-003-doering-methodology.md`
Purpose: Academic methodology reference for chapter structure and citation logic.

## Extraction Notes

- Pages 14-18 contain table-heavy material and may require manual review.

## Content

...
```

## 13. Readiness Gate

Vor dem Build zeigt Amadeus eine Zusammenfassung.

Pflichtinhalt:

- Projektname,
- Zielordner,
- Hauptziel,
- geplanter ausfuehrender Agent,
- empfangene Materialien,
- fehlende Materialien,
- offene Blocker,
- dokumentierte Annahmen,
- geplante Workspace-Struktur,
- geplante Master-Dateien.

Amadeus startet den Build erst, wenn:

- keine Blocker offen sind, oder
- der User explizit erlaubt, mit dokumentierten Annahmen fortzufahren.

## 14. Workspace Build

Der Build ist die Arbeitsphase. Sie beginnt erst nach der Kontextphase.

Amadeus erstellt lokal den finalen Handoff-Workspace.

Standardstruktur:

```text
target_project/
├── CLAUDE.md
├── AGENTS.md
├── MASTER_PROMPT.md
├── PROJECT_BRIEF.md
├── REQUIREMENTS.md
├── DECISIONS.md
├── NEXT_STEPS.md
├── CONTEXT_INDEX.md
├── SOURCE_MAP.md
├── _context/
├── _sources/
├── _skills/
├── _versions/
└── _logs/
```

Englische Namen sind Pflicht, weil sie fuer Gemma, Codex, Claude Code und andere Agenten stabiler sind.

## 15. Dateirollen im Handoff-Workspace

### 15.1 `CLAUDE.md`

Das Herz und Gehirn des Workspaces fuer Claude Code und Claude-aehnliche Agents.

Pflichten:

- sofortige Rolle des ausfuehrenden Agents,
- Zielbild,
- harte Verbote,
- Status,
- Arbeitsphasen,
- Quicklinks,
- File Mapping,
- Regeln zum Lesen grosser Quellen,
- Skills,
- Qualitaetskriterien,
- Verification Checklist,
- Versionierungsregeln,
- Startanweisung.

### 15.2 `AGENTS.md`

Codex-/Agent-kompatible Arbeitsregeln.

Pflichten:

- knappe technische Arbeitsregeln,
- Projektstruktur,
- Test-/Build-Kommandos, falls vorhanden,
- Umgang mit Kontextdateien,
- Definition of Done,
- Arbeitsreihenfolge.

`AGENTS.md` darf `CLAUDE.md` nicht ersetzen. Es ist ein kompatibler Zweit-Einstieg fuer andere Agents.

### 15.3 `MASTER_PROMPT.md`

Der aus Voice/Text kompilierte professionelle Prompt.

### 15.4 `PROJECT_BRIEF.md`

Kurze, klare Projektbeschreibung fuer schnelles Re-Orientieren.

### 15.5 `REQUIREMENTS.md`

Strukturierte Anforderungen und Nicht-Ziele.

### 15.6 `DECISIONS.md`

Alle getroffenen Entscheidungen, Annahmen und deren Begruendung.

### 15.7 `NEXT_STEPS.md`

Konkreter Arbeitsplan fuer den ausfuehrenden Agenten.

### 15.8 `CONTEXT_INDEX.md`

Navigation ueber alle Kontextdateien.

### 15.9 `SOURCE_MAP.md`

Mapping:

```text
original source -> converted markdown -> purpose -> where referenced
```

### 15.10 `_context/`

KI-optimierte Markdown-Versionen aller Materialien.

### 15.11 `_sources/`

Unveraenderte Originaldateien.

### 15.12 `_skills/`

Skills, Regeln, Spezialanweisungen, importierte Dokumentationsmuster.

### 15.13 `_versions/`

Snapshots und Fallbacks bei grossen Aenderungen.

### 15.14 `_logs/`

Transkripte, Verarbeitungsschritte, Warnungen, Build-Protokolle.

## 16. Anatomie der Master-`CLAUDE.md`

Die existierende Erkenntnis aus `amadeus/REQUIREMENTS.md` bleibt zentral. Die `CLAUDE.md` muss als State Machine fuer den ausfuehrenden Agenten funktionieren.

Pflichtsaeulen:

1. Alignment: Rolle und Persona.
2. Constraints: harte Verbote.
3. Session Continuity: Status, Version, naechster Schritt.
4. Semantic File Mapping: jede Datei mit Zweck.
5. Quicklinks: praezise Links auf relevante Abschnitte.
6. Prompt Modularity: Skills und Spezialregeln auslagern.
7. Tool Rules: wie Quellen gelesen werden sollen.
8. Quality Rubrics: Definition von Perfektion.
9. Micro-Workflows: vor Aktion pruefen, loggen, validieren.
10. Verification Engine: Checklisten und Done-Kriterien.

## 17. Versionierung

Bei grossen Aenderungen speichert Amadeus automatisch Snapshots.

Beispiele fuer grosse Aenderungen:

- neuer Master Prompt,
- neue finale `CLAUDE.md`,
- neue Quellenbasis,
- Build-Phase gestartet,
- User aendert Projektziel,
- wesentliche Annahme wird ersetzt.

Snapshot-Struktur:

```text
_versions/
└── 2026-05-24_1530/
    ├── CLAUDE.md
    ├── AGENTS.md
    ├── MASTER_PROMPT.md
    ├── PROJECT_BRIEF.md
    ├── REQUIREMENTS.md
    └── DECISIONS.md
```

## 18. Handoff

Amadeus kommuniziert nicht live mit Codex oder Antigravity. Der Workspace ist das Uebergabeprotokoll.

Startanweisung fuer den ausfuehrenden Agenten:

```md
Read `CLAUDE.md` first.
If you are Codex or another generic coding agent, also read `AGENTS.md`.
Then read `PROJECT_BRIEF.md`, `NEXT_STEPS.md`, and `CONTEXT_INDEX.md`.
Use source material only through `_context/` unless original files are explicitly required.
Execute `NEXT_STEPS.md` from top to bottom.
```

Optional kann Amadeus den fertigen Ordner in VS Code, Codex oder Antigravity oeffnen. Das ist Komfort, nicht Kernarchitektur.

## 19. Grenzen und Fallbacks

### 19.1 Kein automatischer ChatGPT-Transcriber als Kern

ChatGPT-Web oder ChatGPT-Voice wird nicht als automatischer kostenloser Backend-Dienst eingeplant. Das waere fragil und keine stabile lokale Architektur.

Moeglicher optionaler manueller Fallback:

```text
User transcribes manually with ChatGPT -> sends text back to Amadeus
```

### 19.2 Kein automatischer Claude.ai-Reasoning-Proxy als Kern

Claude.ai-Websteuerung wird nicht als Pflichtweg eingeplant. Sie waere fragil, nicht lokal und nicht sauber automatisierbar.

Moeglicher optionaler manueller Premium-Review:

```text
Amadeus exports PROMPT_REVIEW_FOR_CLAUDE.md
User pastes it into Claude.ai
User sends improved text back to Amadeus
Amadeus imports and records it
```

### 19.3 Gemma E4B ist stark, aber nicht allmaechtig

Amadeus darf Gemma nicht mit einem einzigen Monsterprompt alles frei erfinden lassen.

Stattdessen:

- kleine Teilaufgaben,
- strukturierte Outputs,
- feste Templates,
- Validatoren,
- Rueckfragen,
- Versionierung,
- Human Approval Gates.

## 20. Akzeptanzkriterien

Der Workflow ist erfolgreich, wenn:

- der User per Telegram Voice ein Projekt starten kann,
- die Voice kostenlos lokal transkribiert wird,
- Rohtranskript und bereinigte Fassung erhalten bleiben,
- Amadeus einen professionellen Master Prompt erstellt,
- Amadeus fehlende Materialien proaktiv anfragt,
- PDFs/DOCX/MD/TXT in KI-faehiges Markdown ueberfuehrt werden,
- Originale unveraendert erhalten bleiben,
- der finale Workspace englische Agent-Konventionen nutzt,
- `CLAUDE.md` den Ordner als Gehirn vollstaendig abbildet,
- `AGENTS.md` Codex-kompatible Arbeitsregeln enthaelt,
- `SOURCE_MAP.md` und `CONTEXT_INDEX.md` alle Materialien auffindbar machen,
- `_versions/` Fallbacks fuer grosse Aenderungen enthaelt,
- Codex/Claude Code/Antigravity den Workspace ohne manuelle Kontextsuche verwenden kann.

## 21. Quellen und technische Basis

- Gemma 4 Modellfamilie und E4B-Kontext: https://deepmind.google/models/gemma/gemma-4/
- Ollama Gemma 4 Modell-Tags: https://ollama.com/library/gemma4
- OpenAI Whisper Open-Source-Modell: https://github.com/openai/whisper
- faster-whisper lokale Transkription: https://github.com/SYSTRAN/faster-whisper
- Telegram Bot API fuer Voice/File-Download: https://core.telegram.org/bots/api
- Claude Code Memory / `CLAUDE.md` Konzept: https://docs.anthropic.com/en/docs/claude-code/memory
