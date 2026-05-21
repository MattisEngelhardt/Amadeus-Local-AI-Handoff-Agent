# Amadeus: Voice-to-Context Workflow Requirements

Dieses Dokument hält die exakten Workflow-Anforderungen, das Problemverständnis und die Systemziele für das Projekt "Amadeus" fest. Es dient als absolute Single Source of Truth für alle Architektur-Entscheidungen.

## 1. Problemstellung (Der aktuelle manuelle Workflow)
Derzeit erfordert der Start eines neuen Projekts oder einer komplexen Aufgabe in Antigravity (VS Code + Claude Code) massive manuelle Vorarbeit. Der Prozess läuft wie folgt ab:
1. Sprachaufnahme via ChatGPT Mobile (aufgrund der exzellenten deutschen Speech-to-Text Erkennung).
2. Manuelles Copy-Paste des generierten Transkripts in das Web-UI von Claude (Modell: Sonnet 4.7 oder Opus).
3. Händisches Prompt-Engineering (Anweisungen an Claude: "Dies ist ein unstrukturierter Text. Erstelle daraus einen perfekten, 10-seitigen strukturierten Master-Prompt.").
4. Manuelles Erstellen der Ziel-Ordnerstruktur im lokalen Dateisystem.
5. Manueller Upload und Formatierung von Kontext-Dokumenten (z. B. PDFs in lesbares Markdown).
6. Erstellen einer initialen `CLAUDE.md` und Einfügen des generierten Master-Prompts.
7. Erst danach kann Claude Code im VS Code Terminal gestartet werden.

**Kritikpunkt:** Dieser Prozess ist hochgradig repetitiv, verlangt ständige Kontextwechsel und verschwendet durch Copy-Paste-Routinen wertvolle Entwicklungszeit.

## 2. Zielsetzung (Der Amadeus Workflow)
Amadeus ist ein spezialisierter "Prep-Agent", der die manuellen Vorbereitungsschritte (1 bis 6) vollständig eliminiert. Er konsumiert unstrukturierte Sprachnachrichten sowie rohe Dokumente und produziert autonom einen fehlerfreien, "Antigravity-ready" Projektordner.

### Phase 1: Ingestion & Gap-Analysis (Interaktiv)
- **Voice Input:** Die Anforderungsaufnahme erfolgt über ein minimalistisches Desktop-UI (Floating Bar). Zur Verarbeitung wird die OpenAI Whisper API genutzt, um eine makellose Transkription zu garantieren.
- **Context Drop:** Begleitende Dokumente (PDFs, Word) können per Drag & Drop in das Interface geladen werden.
- **Agent Reflection (Pushback):** Amadeus analysiert das Transkript in Relation zu den bereitgestellten Dokumenten und validiert: *"Habe ich alle Informationen, um einen perfekten Mega-Prompt zu schreiben?"*
- **Targeted Questions:** Erkennt das LLM inhaltliche Lücken (z.B. fehlende Referenz-Dateien, unklare Zielarchitektur), blockiert es den weiteren Prozess und formuliert gezielte Rückfragen.
- **Iteration:** Über weitere Sprachnachrichten werden die fehlenden Parameter nachgereicht, bis das System die Anforderungen als "vollständig" flaggt.

### Phase 2: Deep Prep (Autonomer Hintergrundprozess)
Nach Abschluss der Ingestion arbeitet das System autonom:
- **Document Formatting:** Sämtliche Rohdateien (PDFs, Word-Docs) werden durch Parser in sauberes, semantisches Markdown (`.md`) konvertiert. Dies ist eine harte technische Anforderung, da LLMs Markdown-Strukturen weitaus präziser und token-effizienter verarbeiten.
- **Mega-Prompt Synthesis:** Ein starkes Reasoning-Modell (z.B. lokales DeepSeek-R1 via Ollama oder Anthropic/Groq APIs) transformiert die transkribierten Voice-Notizen in einen hochstrukturierten Master-Prompt.

### Phase 3: Workspace Scaffolding & Handoff
- **Folder Creation:** Das System instanziiert den physischen Zielordner auf der Festplatte.
- **Context Injection:** Die konvertierten Markdown-Referenzen werden isoliert im Unterverzeichnis `/_context` gespeichert.
- **Master `CLAUDE.md`:** Das finale Kernstück wird generiert (siehe Kapitel 4).
- **Handoff:** Der vorbereitete Ordner wird in Antigravity geöffnet. Ein einziger Start-Befehl an Claude Code genügt, um die fehlerfreie Ausführung auf Basis der optimalen Vorarbeit zu triggern.

## 3. Architektur-Prinzipien
- **Keine Halluzinationen:** Der Agent trifft bei Unsicherheiten keine eigenmächtigen Annahmen, sondern forciert den Pushback-Loop.
- **Markdown-First:** Jeglicher Kontext für das LLM muss zwingend in strukturiertem Markdown vorliegen.
- **Asynchronität:** Die Deep Prep Phase darf das OS oder die UI nicht blockieren.
- **Kein Code-Generator:** Amadeus schreibt keine produktiven App-Dateien (`.py`, `.js`). Er liefert ausschließlich Spezifikationen, Prompts und Kontext-Mappings. Die exekutive Implementierung obliegt immer Claude Code in Antigravity.

---

## 4. Die Anatomie der Master-CLAUDE.md (Der Goldstandard)

Das ultimative Output-Ziel von Amadeus ist die Generierung einer `CLAUDE.md`, die das "Herz und Gehirn" des Zielprojekts ist. Ein normaler Prompt verliert nach einem Neustart den Faden. Eine von Amadeus generierte Master-CLAUDE.md hingegen fungiert als **Zustandsmaschine (State Machine)**. Sie muss strikt den folgenden **10 architektonischen Säulen** folgen, um Claude Code auch über dutzende Sessions hinweg fehlerfrei zu orchestrieren:

### I. Das Alignment (Persona & Pitch)
Das Dokument beginnt zwingend mit der sofortigen Kalibrierung des LLMs. 
- **Was:** Zuweisung einer exakten Rolle (z.B. "Du bist ein Senior Game Developer" oder "Du bist ein akademischer Ghostwriter").
- **Warum:** Reduziert den semantischen Suchraum des Modells sofort auf die gewünschte Domäne und definiert den roten Faden des Projekts.

### II. Die Leitplanken (Verbindliche Verbote / Constraints)
Eine harte Abgrenzung dessen, was das LLM **nicht** tun darf.
- **Was:** Eine unmissverständliche *Do-Not-Do*-Liste (z.B. "Verwende keine Original-PDFs", "Erfinde keine empirischen Daten", "Ignoriere den .venv Ordner").
- **Warum:** Generative KIs neigen zu Halluzinationen. Diese Sektion dient als harte Absicherung (Bounding Box), um den Projekt-Scope zu schützen.

### III. Session-Kontinuität & Temporalität (State Tracking)
Die Fähigkeit, nach einem Neustart exakt dort weiterzumachen, wo die KI aufgehört hat.
- **Was:** Explizite Versionierungen (z.B. `Version 2.0.0 | Letzte Aktualisierung...`), Sektionen wie "Statusübersicht" oder Verlinkungen zu einer `NEXT_STEPS.md`. Das Dokument hält fest, was die *übergeordnete Aufgabe* ist, *bei welchem Schritt* man sich befindet und was *noch zu tun* ist.
- **Warum:** Verhindert Amnesie und zeitliche Desorientierung. Das LLM lädt bei jedem Start sofort den "Spielstand".

### IV. Semantisches File-Mapping (Die Quellen-Rollen)
Dateien werden nicht nur verlinkt, sondern mit Bedeutung aufgeladen.
- **Was:** Statt nur einen Pfad zu nennen, wird erklärt: *Warum* gibt es diese Datei? *Was* ist ihre Rolle? *Wann* darf sie benutzt werden?
- **Warum:** Das LLM versteht die Architektur des Projekts und weiß genau, welches Dokument für welche Fragestellung maßgeblich ist.

### V. Präzise Quicklinks & Anchor-Navigation (Das neuronale Netz)
Das Dokument verbindet alle Projekt-Dateien perfekt miteinander und erlaubt millimetergenaue Navigation.
- **Was:** Es reicht nicht, nur auf eine Zieldatei zu verlinken. Es müssen zwingend **präzise Quicklinks mit Anchor-Tags** (`[Thema X](datei.md#kapitel-3)`) verwendet werden, die den Nutzer (und die KI) mit einem Klick exakt auf den relevanten Abschnitt im Ziel-Dokument bringen.
- **Warum:** Maximale Effizienz und Schutz des Context-Windows. Weder Mensch noch KI müssen in langen Dokumenten suchen oder scrollen. Der Quicklink liefert sofort und zielgenau den exakten Kontext-Ausschnitt, der in dieser Sekunde benötigt wird.

### VI. Prompt-Modularität (Skill-Delegation)
Das Master-Dokument ist kein Monolith, sondern ein Hypervisor.
- **Was:** Auslagern spezifischer Regelwerke (z.B. Godot-Framework-Regeln, Zitier-Richtlinien) in externe Markdown-Dateien (z.B. `_agent/skills/GODOT_SKILL.md`).
- **Warum:** Hält das Hauptdokument extrem schlank. Das LLM lädt das spezifische Regelwerk nur dann, wenn es den entsprechenden Skill gerade ausführen muss.

### VII. Spezifische Werkzeug-Regeln (Interaktions-Logik)
Metadaten darüber, *wie* Kontext-Dateien konsumiert werden sollen.
- **Was:** Explizite Suchanweisungen (z.B. "Döring nie vollständig laden, immer per Grep suchen").
- **Warum:** Verhindert Timeout-Fehler oder Abstürze von Claude Code beim Versuch, massive Textmengen auf einmal zu parsen.

### VIII. Der Qualitäts-Maßstab (Evaluation Rubrics & Blueprints)
Das LLM bekommt nicht nur die Aufgabe, sondern die genaue Definition von "Perfektion".
- **Was:** Strikte Output-Schemata (Blueprint-Gliederungen) und Bewertungskriterien (z.B. Punkteverteilungen für Hausarbeiten).
- **Warum:** Die KI kennt dadurch die "Definition of Done" in perfekter Schärfe und bewertet ihre eigenen Outputs, bevor sie diese als fertig deklariert.

### IX. Micro-Workflows & Forced Reflection (Der Zwang zum Denken)
Das Unterbinden vorschneller Aktionen durch erzwungene Dokumentation.
- **Was:** Das LLM wird gezwungen, *vor* einer Aktion ein Logbuch oder eine Tabelle auszufüllen (z.B. "Zitationsmatrix ausfüllen vor dem Zitieren", "Bug-Protokoll führen").
- **Warum:** Dies zwingt das LLM in ein *Chain-of-Thought*-Muster. Erst nachdenken und dokumentieren, dann handeln. Reduziert Flüchtigkeitsfehler gegen Null.

### X. Verifikation & Execution Engine (Der Motor)
Ein klar strukturiertes, binäres Ausführungs-Framework am Ende des Dokuments.
- **Was:** Checklisten mit klaren Status-Zuweisungen ("OFFEN", "ERLEDIGT") und Schritt-für-Schritt Blaupausen.
- **Warum:** Das LLM muss nicht iterativ raten, was der nächste Schritt ist. Es evaluiert seine Arbeit gegen die Checkliste, dokumentiert den Fortschritt und geht systematisch zum nächsten Punkt über.
