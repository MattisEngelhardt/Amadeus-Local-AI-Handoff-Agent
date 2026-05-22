# Lokale AI & Autonome Agenten: Das Ultimative Handbuch für Production-Grade Engineering
### Ein tiefgehender Architektur-Leitfaden für Qwen 3.6, llama.cpp, Pydantic & die Vermeidung typischer Integrationsfehler

Dieses Dokument dient als das **definitive Referenzhandbuch** für die Konzeption, den Betrieb und die Skalierung **vollständig lokaler, souveräner KI-Agenten**. Es beleuchtet sowohl die theoretischen Grundlagen (Hardware-Sizing, Quantisierung) als auch die harten praktischen Realitäten von lokalen LLMs in Agenten-Workflows – insbesondere die Integration der hochmodernen **Qwen 3.6** Modellreihe – und zeigt konkrete Code-Patterns zur Lösung von XML/Reasoning-Fehlern in Entwicklungs-Pipelines.

---

```
                       [Benutzer-Audio / Sprache]
                                    │
                                    ▼
                 [faster-whisper STT (Lokal & Offline)]
                                    │
                                    ▼
                 [Strukturierte Extraktion mit Pydantic]
                  Mode.MD_JSON / Qwen 3.6 / Instructor
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
      [Loggt & speichert <think>]           [Valide JSON-Daten]
         Traces auf die Disk                   für den Agenten
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
                        [Projekt-Code-Generator]
                                    │
                                    ▼
                      [Regex 'Think-Tag' Scrubbers]
                                    │
                                    ▼
                        [Syntaktisch valider Code]
                        Verhindert SyntaxErrors
```

---

## 1. Lokale AI & Agenten: Die Architektur-Philosophie

Die Migration von Cloud-basierten APIs (wie Anthropic Claude oder Google Gemini) hin zu einer autarken, lokalen KI-Agenten-Architektur ist weit mehr als der Austausch von Base-URLs – es ist ein fundamentaler Paradigmenwechsel im Software-Design.

### Warum der Wechsel zu 100% lokal?
1. **Absolute Datenhoheit (Zero-Trust Sovereignty):** Der gesamte Code, firmeneigene Designdokumente, API-Schemata und Datenbank-Strukturen verlassen niemals den physischen Rechner des Entwicklers.
2. **Kosten-Determinismus auf Enterprise-Niveau:** Während ein Agenten-Loop (bestehend aus mehrstufigen Reflexions- und Validierungs-Schritten) in der Cloud Hunderte von Dollar pro Tag an Token-Kosten verursachen kann, läuft das lokale System nach der Hardware-Anschaffung völlig kostenlos.
3. **Kontext-Souveränität:** Die Qwen 3.6 Modellreihe unterstützt Kontextfenster von bis zu **128.000 Token** nativ. Lokale Runner ermöglichen Prompt-Caching, wodurch Gigabytes an Codebasis-Dateien ohne spürbare Latenz als permanenter Kontext geladen bleiben.

---

## 2. Hardware-Sizing & Die Mathematik des VRAM-Bedarfs

Ein kritischer Fehler bei der Planung lokaler Agenten ist das fehlerhafte Hardware-Sizing. Fällt das Modell mangels VRAM auf die CPU zurück (CPU Fallback), bricht die Verarbeitungsgeschwindigkeit von 40+ Token/s auf unbenutzbare 0.5–2 Token/s zusammen.

### Mathematische Formel zur VRAM-Berechnung

Der Gesamt-VRAM-Bedarf setzt sich aus dem **Modellgewicht** und dem dynamischen **KV-Cache (Key-Value-Speicher)** zusammen:

$$\text{VRAM}_{\text{total}} \approx \left( \frac{\text{Parameter (Milliarden)} \times \text{Quantisierungs-Bits}}{8} \times 1.15 \right) + \text{VRAM}_{\text{KV-Cache}}$$

Der Faktor $1.15$ repräsentiert einen Puffer von 15% für CUDA-Overhead und System-Bibliotheken.

Der **KV-Cache** wächst linear mit der Kontextlänge ($C$ in Token), der Anzahl der Schichten ($N_{\text{layers}}$), der Anzahl der Attention-Heads ($N_{\text{heads}}$) und der Head-Dimension ($D_{\text{head}}$):

$$\text{VRAM}_{\text{KV-Cache}} \approx 2 \times 2 \times N_{\text{layers}} \times N_{\text{heads}} \times D_{\text{head}} \times C \times 2 \text{ Bytes (FP16)}$$

> [!NOTE]
> Die Verwendung von **Grouped-Query Attention (GQA)** in modernen Modellen wie Qwen 3.6 reduziert diesen Cache-Footprint um den Faktor 8 und ermöglicht massive Kontexte auf Consumer-GPUs.

### Sizing- & Quantisierungs-Matrix

| Modell-Größe | Quantisierung | Disk-Größe | Benötigter VRAM | Max. Kontext | Target Hardware |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 7B-Instruct** | `Q5_K_M` (5-bit) | ~5.1 GB | ~6.5 GB | 32,768 | RTX 3060/4060, Apple M1/M2/M3 (16GB RAM) |
| **Qwen 14B-Instruct** | `Q4_K_M` (4-bit) | ~9.2 GB | ~11.0 GB | 32,768 | **Süßpunkt (Sweetspot):** RTX 4070 12GB, Apple Max 32GB |
| **Qwen 27B-Instruct** | `Q4_K_M` (4-bit) | ~19.5 GB | ~22.0 GB | 16,384 | RTX 3090/4090 24GB, Apple Max 48GB+ |
| **Qwen 72B-Instruct** | `Q3_K_L` (3-bit) | ~34.0 GB | ~38.0 GB | 8,192 | 2x RTX 3090/4090, Apple Ultra 64GB+ |

---

## 3. Deployment OHNE Ollama (Direkte GGUF-Downloads & native Runner)

Ollama ist ein hervorragender Wrapper, kapselt das LLM jedoch in eine Blackbox und limitiert tiefere Server-Optimierungen. Für maximale Performance in Agenten-Pipelines empfiehlt sich die native Ausführung nackter **GGUF-Dateien** über High-Performance-Laufzeitumgebungen.

### A. Download-Quellen für GGUF-Modelle
1. **Hugging Face (Die weltweite Primärquelle):**
   - Suche nach offiziellen Repositories (z. B. `Qwen/Qwen3.6-27B-Instruct-GGUF`) oder optimierten Community-Builds von Experten wie **Bartowski** (`Bartowski/Qwen3.6-27B-Instruct-GGUF`).
   - Navigiere zu *Files and versions* und lade die gewünschte Datei (z. B. `qwen3.6-27b-instruct-q4_k_m.gguf`) direkt herunter.
2. **LM Studio In-App Search:**
   - LM Studio bietet eine integrierte Suche, die direkt auf Hugging Face zugreift und die Modelle mit einem einzigen Klick im richtigen lokalen Verzeichnis abspeichert.
3. **ModelScope (Alibaba Mirror):**
   - Falls die Bandbreite von Hugging Face gedrosselt ist, bietet ModelScope eine extrem schnelle Alternative für offizielle Qwen-Releases.

---

### B. High-Performance Hosting-Optionen

#### Methode 1: Native Windows `llama.cpp` Compilation (Empfohlen für maximale Performance)
Durch das Kompilieren von `llama.cpp` mit CUDA-Beschleunigung unter Windows werden Latenzen minimiert und modernste Kernel-Treiber optimal ausgenutzt.

```powershell
# Repository klonen
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# CMake mit aktivierter CUDA-Hardwarebeschleunigung konfigurieren
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release

# Kompilieren mit allen verfügbaren CPU-Kernen
cmake --build build --config Release --clean-first
```

> [!WARNING]
> **Der llama-server Reasoning-Truncation Bug:**
> Lokale Runner wie `llama-server` besitzen integrierte Parser, um DeepSeek-ähnliche `<think>`-Tags zu extrahieren. Da Qwen 3.6 jedoch dynamische Denk-Muster besitzt, kann dieser Parser abstürzen und die Generation unmittelbar nach dem Denkprozess stumm abschneiden (**Silent Truncation**).
> **Lösung:** Deaktivieren Sie den server-seitigen Parser über `--reasoning-format none` und filtern Sie die Tags kontrolliert in Python!

**Optimierter Start-Befehl (Terminal):**
```powershell
.\build\bin\Release\llama-server.exe `
  -m "C:\Models\Qwen3.6-27B-Instruct-Q4_K_M.gguf" `
  -c 32768 `
  -ngl 99 `
  -fa `
  --reasoning-format none `
  --prompt-cache "C:\Models\amadeus_cache.bin" `
  --prompt-cache-all `
  --ctx-shift
```
*   `-ngl 99` (`--n-gpu-layers`): Schiebt alle 99 Modellschichten vollständig in den GPU-VRAM.
*   `-fa` (`--flash-attn`): Aktiviert FlashAttention, was den VRAM-Verbrauch des KV-Caches halbiert.
*   `--prompt-cache`: Speichert den System-Prompt im Speicher. Reduziert die Analyse-Verzögerung bei wiederholten Aufrufen von Sekunden auf **unter 5 Millisekunden**.

#### Methode 2: LM Studio (Die unkomplizierte GUI-Alternative)
1. Laden Sie das Modell über die In-App-Suche herunter.
2. Wählen Sie im rechten Panel unter **GPU Acceleration** Ihre NVIDIA-Grafikkarte aus und schieben Sie den Schieberegler auf Max (vollständiges Offloading).
3. Starten Sie im Server-Tab den lokalen, OpenAI-kompatiblen Port (Standard: `http://localhost:1234/v1`).

---

## 4. Die Klippe lokaler Agenten: Das Reasoning-Modell-Dilemma

Moderne Reasoning-Modelle (wie Qwen 3.6 und DeepSeek-R1) nutzen **Chain-of-Thought (CoT)**, um komplexe Probleme vor der Antwortgenerierung strukturiert zu durchdenken. Dies geschieht in Form von XML-Tags:

```xml
<think>
Der Benutzer möchte eine App-Struktur extrahieren.
Ich muss ein valides JSON zurückgeben, das dem Pydantic-Schema entspricht.
1. display_name = "Finance Tracker"
2. files_to_create = [...]
...
</think>
{
  "display_name": "Finance Tracker",
  "files_to_create": []
}
```

### Das Problem: JSON-Dekodierungsfehler & Syntax-Korruption

1. **Structured Output Crash (JSONDecodeError):**
   Wird diese Ausgabe direkt an einen JSON-Parser (wie `json.loads`) übergeben, stürzt das Skript sofort mit einem fatalen Fehler ab:
   `json.decoder.JSONDecodeError: Unexpected character: '<' at line 1 column 1`
2. **Dateisystem-Korruption (SyntaxError):**
   Soll der Agent Code für eine Datei (z. B. `app.py`) generieren, bettet er oft seinen `<think>`-Prozess direkt in den Dateiinhalt ein. Der Agent speichert dies auf der Festplatte ab, was beim Ausführen des Codes zu folgendem Fehler führt:
   `SyntaxError: invalid syntax` (aufgrund der XML-Zeichen auf Zeile 1).

---

## 5. Robuste Software-Engineering-Lösungen in Python

Um lokale Agenten abzusichern, müssen wir die XML-Denkprozesse proaktiv abfangen, protokollieren und eliminieren, bevor Daten an Parser oder das Dateisystem übergeben werden.

### Lösung A: Verwendung des `instructor`-Frameworks mit `MD_JSON`

Das beliebte `instructor`-Paket von Jason Liu erlaubt die nahtlose Kopplung von Pydantic-Klassen mit LLM-Antworten. Für lokale Modelle, die Markdown-Blöcke und XML-Denkprozesse ausgeben, ist der Modus `instructor.Mode.MD_JSON` der Lebensretter. Er instruiert den Parser, nach ` ```json ... ``` ` Blöcken zu suchen und den davor liegenden Text (inklusive `<think>`) zu ignorieren.

```python
from openai import OpenAI
import instructor
from pydantic import BaseModel

class ProjectSchema(BaseModel):
    display_name: str
    version: str

# Initialisierung des lokalen Instructor-Clients
base_client = OpenAI(base_url="http://localhost:8080/v1", api_key="local")
client = instructor.from_openai(base_client, mode=instructor.Mode.MD_JSON)

# Sicherer strukturierter Aufruf
project = client.chat.completions.create(
    model="qwen3.6-27b",
    response_model=ProjectSchema,
    messages=[
        {"role": "user", "content": "Generiere eine Projektstruktur für einen Finance-Tracker."}
    ]
)
```

---

### Lösung B: Manueller Regex-Sicherheitsfilter & Observability-Logging

In hochgradig angepassten Systemen empfiehlt sich ein manueller Preprocessor. Dieser extrahiert den Denkprozess (`<think>...</think>`), schreibt ihn zur Analyse in eine **Observability-Logdatei** (wichtig für das Debugging lokaler Agenten) und bereinigt den Payload für den JSON-Parser.

```python
import re
import json
import logging

logger = logging.getLogger("agent.observability")

def process_and_parse_response(raw_response: str):
    # 1. Denkprozess isolieren und in separate Logdatei schreiben
    think_match = re.search(r"<think>(.*?)</think>", raw_response, re.DOTALL)
    if think_match:
        cot_trace = think_match.group(1).strip()
        logger.info(f"--- LOCAL LLM CHAIN-OF-THOUGHT TRACE ---\n{cot_trace}\n--------------------------------------")
        
    # 2. XML-Denk-Tags vollständig aus dem Payload entfernen
    cleaned_payload = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()
    
    # 3. Markdown Code-Block Umrandungen bereinigen
    markdown_block = re.search(r"```json\s*(.*?)\s*```", cleaned_payload, re.DOTALL)
    if markdown_block:
        cleaned_payload = markdown_block.group(1).strip()
        
    # 4. Sichere Konvertierung in Python-Dictionary
    return json.loads(cleaned_payload)
```

---

### Lösung C: Code-Scaffolding Schutz (Verhinderung korrupter Skripte)

Vor dem finalen Schreiben von generiertem Code auf die Festplatte muss der Agent einen Desinfektions-Filter durchlaufen. Dies stellt sicher, dass kein lokal generiertes Python-Skript durch eingestreute Denkprozesse oder Markdown-Wrapper unbrauchbar wird.

```python
def sanitize_code_payload(raw_code: str) -> str:
    # 1. Entferne eventuell generierte Denktraces
    clean_code = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
    
    # 2. Säubere Code von Markdown-Umrandungen (z. B. ```python)
    if clean_code.startswith("```"):
        lines = clean_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean_code = "\n".join(lines).strip()
        
    return clean_code
```

---

## 6. Vollständiger, lokaler Python-Integration-Blueprint

Dieser lauffähige Blueprint zeigt, wie die Klassen `TranscriptAnalyzer` (Strukturierte Extraktion aus Sprache) und `ProjectGenerator` (Dateierstellung) erweitert werden, um nahtlos und fehlerfrei mit lokalen Modellen wie Qwen 3.6 oder Cloud-Modellen als Fallback zu interagieren.

### A. Lokaler Transcript-Analyzer (`analyzer.py`)

```python
import os
import logging
import json
import re
import yaml
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self, api_key=None, config_path=None):
        load_dotenv()
        self.client = None
        self.quality_criteria = []
        
        # Lokale Standardwerte definieren
        self.llm_provider = "local"
        self.local_api_base = "http://localhost:8080/v1"
        self.model = "qwen3.6-27b-instruct"
        self.local_temperature = 0.1
        self.local_max_retries = 3

        # Konfiguration laden, falls vorhanden
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    self.quality_criteria = config.get("quality_criteria", [])
                    models_cfg = config.get("models", {})
                    self.llm_provider = models_cfg.get("llm_provider", "local")
                    
                    if self.llm_provider == "local":
                        local_cfg = models_cfg.get("local", {})
                        self.local_api_base = local_cfg.get("api_base", "http://localhost:8080/v1")
                        self.model = local_cfg.get("model_name", "qwen3.6-27b-instruct")
                        self.local_temperature = local_cfg.get("temperature", 0.1)
                        self.local_max_retries = local_cfg.get("max_retries", 3)
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}")

        # Client-Initialisierung basierend auf dem Provider
        if self.llm_provider == "local":
            logger.info(f"Initialisiere lokalen Instructor-Client an: {self.local_api_base}")
            base_client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
            # MD_JSON Modus fängt Qwen-Denktraces und Markdown-Formatierungen sauber ab
            self.client = instructor.from_openai(base_client, mode=instructor.Mode.MD_JSON)
        else:
            # Fallback zu Anthropic Claude Cloud-API
            from anthropic import Anthropic
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.client = Anthropic(api_key=self.api_key)

    def _strip_thinking_tags(self, text: str) -> str:
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            # Schreibt den Denkprozess in die Anwendungslogs zur Analyse
            logger.info(f"Captured Local LLM CoT:\n{think_match.group(1).strip()}")
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def analyze(self, transcript_text: str) -> RequirementsModel:
        if not transcript_text:
            logger.error("Transkript-Text ist leer.")
            return None

        system_prompt = """Du bist ein Senior-Softwarearchitekt. Analysiere das rohe Entwickler-Transkript.
Extrahiere und strukturiere einen umfassenden Projektplan im geforderten Format.
Füge sinnvolle Hilfsdateien hinzu (z. B. pytest-Tests, README, config.yaml, .env), 
die für ein vollwertiges Boilerplate-Projekt unumgänglich sind."""

        if self.llm_provider == "local":
            try:
                # Nutzt Instructor für die strukturierte Extraktion über die lokale API
                requirements = self.client.chat.completions.create(
                    model=self.model,
                    response_model=RequirementsModel,
                    temperature=self.local_temperature,
                    max_retries=self.local_max_retries,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Transkript:\n\n{transcript_text}"}
                    ]
                )
                return requirements
            except Exception as e:
                logger.error(f"Instructor-Extraktion fehlgeschlagen: {e}. Starte Regex-Fallback...")
                return self._fallback_manual_parse(transcript_text, system_prompt)
        else:
            # Claude Cloud-API Logik
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": transcript_text}],
                tools=[{
                    "name": "save_requirements",
                    "description": "Speichert die strukturierten Anforderungen.",
                    "input_schema": RequirementsModel.model_json_schema()
                }],
                tool_choice={"type": "tool", "name": "save_requirements"}
            )
            tool_use = next(b for b in response.content if b.type == "tool_use")
            return RequirementsModel(**tool_use.input)

    def _fallback_manual_parse(self, transcript_text: str, system_prompt: str) -> RequirementsModel:
        """Sicherheitsnetz bei unerwarteten API-Formatfehlern."""
        try:
            raw_client = OpenAI(base_url=self.local_api_base, api_key="local")
            response = raw_client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nGib strictly ein JSON im Code-Block zurück."},
                    {"role": "user", "content": transcript_text}
                ]
            )
            raw_text = response.choices[0].message.content
            cleaned = self._strip_thinking_tags(raw_text)
            
            markdown_block = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
            if markdown_block:
                cleaned = markdown_block.group(1).strip()
                
            return RequirementsModel(**json.loads(cleaned))
        except Exception as ex:
            logger.critical(f"Totaler Absturz: Auch der Regex-Fallback schlug fehl! {ex}")
            return None
```

---

### B. Lokaler Code-Generator (`generator.py`)

```python
import os
import logging
import re
import yaml
from openai import OpenAI
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel

logger = logging.getLogger(__name__)

class ProjectGenerator:
    def __init__(self, config_path=None):
        load_dotenv()
        self.llm_provider = "local"
        self.local_api_base = "http://localhost:8080/v1"
        self.model = "qwen3.6-27b-instruct"
        self.local_temperature = 0.2

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    models_cfg = config.get("models", {})
                    self.llm_provider = models_cfg.get("llm_provider", "local")
                    
                    if self.llm_provider == "local":
                        local_cfg = models_cfg.get("local", {})
                        self.local_api_base = local_cfg.get("api_base", "http://localhost:8080/v1")
                        self.model = local_cfg.get("model_name", "qwen3.6-27b-instruct")
                        self.local_temperature = local_cfg.get("temperature", 0.2)
            except Exception as e:
                logger.error(f"Laden der Generator-Konfiguration fehlgeschlagen: {e}")

        if self.llm_provider == "local":
            logger.info(f"Verwende lokalen Client für Code-Generierung: {self.local_api_base}")
            self.client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _sanitize_generated_code(self, raw_code: str) -> str:
        # Essenziell: Entferne alle Denkprozesse aus der Code-Datei
        clean_code = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
        
        # Markdown Fences bereinigen
        if clean_code.startswith("```"):
            lines = clean_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_code = "\n".join(lines).strip()
        return clean_code

    def generate_file_content(self, requirements: RequirementsModel, target_file_path: str, file_purpose: str) -> str:
        logger.info(f"Generiere Code für {target_file_path} via {self.llm_provider}...")

        system_prompt = f"""Du bist ein Lead-Softwareentwickler.
Schreibe den vollständigen, syntaktisch korrekten Inhalt für die Datei `{target_file_path}`.
Dateizweck: {file_purpose}

WICHTIG:
1. Nutze KEINE Platzhalter, Abkürzungen oder Kommentare wie '# TODO: Rest implementieren'.
2. Der Code muss sofort lauffähig sein und nahtlos mit anderen Dateien interagieren.
3. Gib NUR den reinen Datei-Inhalt aus. Schreibe keinen einleitenden oder ausleitenden Text.
"""

        if self.llm_provider == "local":
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.local_temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Erstelle den Code für: `{target_file_path}`"}
                    ]
                )
                raw_content = response.choices[0].message.content.strip()
                return self._sanitize_generated_code(raw_content)
            except Exception as e:
                logger.error(f"Fehler bei lokaler Code-Generierung für {target_file_path}: {e}")
                return ""
        else:
            # Claude Cloud-API Generierungs-Logik
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Erstelle den Code für: `{target_file_path}`"}]
            )
            return self._sanitize_generated_code(response.content[0].text.strip())
```

---

## 7. Operationalisierungs- & Validierungs-Checkliste

Um Ihr lokales AI-Agenten-System in Betrieb zu nehmen, gehen Sie systematisch nach dieser Checkliste vor:

- [ ] **Windows-Directory-Junction anlegen:**
  Sichern Sie absolute Namespace-Importe im Projekt ab, ohne den Python-Code zu manipulieren.
  ```powershell
  New-Item -ItemType Junction -Path "speech_to_code" -Target "amadeus"
  ```
- [ ] **VRAM-Kapazitätsprüfung:**
  Ermitteln Sie die VRAM-Größe Ihrer Grafikkarte. Wählen Sie basierend auf der Sizing-Matrix das passende Qwen 3.6 GGUF-Modell (z. B. 14B-Instruct-Q4_K_M für 12GB VRAM GPUs).
- [ ] **llama.cpp / Server-Instanz starten:**
  Stellen Sie sicher, dass FlashAttention aktiviert und der fehlerhafte interne Reasoning-Parser deaktiviert ist.
  ```powershell
  .\llama-server.exe -m "C:\Models\qwen_model.gguf" -c 32768 -ngl 99 -fa --reasoning-format none
  ```
- [ ] **Konfigurationsdatei `config.yaml` umstellen:**
  Tragen Sie den lokalen Provider und die passende API-URL ein.
  ```yaml
  models:
    llm_provider: "local"
    local:
      api_base: "http://localhost:8080/v1"
      model_name: "qwen3.6-27b-instruct"
  ```
- [ ] **Laufzeit-Tests durchführen:**
  Führen Sie das lokale Testsuite-Skript aus, um die Integrität der gesamten Offline-Extraktion und Generierung zu bestätigen.
  ```powershell
  .venv\Scripts\pytest.exe
  ```

---

> [!IMPORTANT]
> **Das Geheimnis lokaler Exzellenz:**
> Lokale Open-Weights-Modelle wie **Qwen 3.6** stehen Cloud-Systemen in nichts nach, solange der Server optimal eingestellt ist (CUDA-Offloading, Prompt-Caching) und die Software-Pipelines Schutzfilter besitzen, um unstrukturierte Chain-of-Thought Ausgaben sauber zu verarbeiten. Nutzen Sie diesen Blueprint als Grundstein für Ihre souveräne Agenten-Infrastruktur!
