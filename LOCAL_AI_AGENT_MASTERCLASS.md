# Amadeus: Local AI Agent Masterclass & Production Architecture (Qwen 3.6)

Dieses Dokument dient als die ultimative, praxisnahe technische Blueprint für den Übergang von Amadeus zu einer **100% lokalen, datenschutzkonformen und hochperformanten Inferenz-Architektur**. Es basiert auf einer detaillierten Code- und Laufzeitanalyse der Repository-Struktur, des virtuellen Environments und der inhärenten Herausforderungen lokaler Inferenz.

---

## 1. Monorepo-Import-Auflösung & Die "speech_to_code" Junction

### Diagnose & Ursache des Import-Konflikts
Das Repository ist als Monorepo aufgebaut, bei dem zwei Desktop-Anwendungen (`amadeus/` und `study_agent/`) eine gemeinsame Daten- und Gatewayschicht nutzen. Beim Ausführen von Tests oder Modulaufrufen trat folgendes Problem auf:
* Alle Importe innerhalb des `amadeus/`-Verzeichnisses (z. B. in `main.py` und `core/analyzer.py`) verwenden absolute Pfade im Format: `from speech_to_code.core.analyzer import ...`.
* Die physische Ordnerstruktur auf dem Datenträger nennt das Verzeichnis jedoch `amadeus/` und nicht `speech_to_code/`.
* Dies führt standardmäßig zu einem fatalen `ModuleNotFoundError: No module named 'speech_to_code'`, da Python den Import-Namensraum nicht auflösen kann.

### Die Zero-Code-Change Lösung
Anstatt Hunderte Import-Zeilen in der gesamten Codebasis anzupassen (was zu Merge-Konflikten und Inkonsistenzen in Versionierungstools führen würde), wurde auf Betriebssystemebene eine hochperformante **Verzeichnisverbindung (Directory Junction)** eingerichtet.

Führen Sie folgenden Befehl im Hauptverzeichnis aus (unter Windows PowerShell bereits etabliert):
```powershell
New-Item -ItemType Junction -Path "speech_to_code" -Target "amadeus"
```

#### Warum das funktioniert:
* Der Windows-Kernel leitet alle Lese- und Schreibzugriffe auf `speech_to_code` transparent an den echten Ordner `amadeus` weiter.
* Für Python-Interpreter und Editoren existiert nun ein virtueller Namensraum `speech_to_code`, was alle absoluten Importe ohne jeden Performance-Verlust augenblicklich repariert.
* In Ihrer IDE können Sie Dateien unter beiden Pfaden aufrufen. Es wird empfohlen, in Git ausschließlich Änderungen im echten Ordner `amadeus/` zu verfolgen.

---

## 2. Das Structured Output Dilemma bei lokalen Reasoning-Modellen (Qwen 3.6)

Lokale High-End-Reasoning-Modelle wie **Qwen 3.6-27B** (oder DeepSeek R1) arbeiten mit einer inhärenten Kette von Überlegungen (Chain-of-Thought, CoT). Diese Modelle schreiben ihre Gedanken in XML-ähnliche Tags (z. B. `<think>...</think>`), bevor sie das eigentliche Ergebnis liefern. 

Dies führt bei automatisierten Agenten-Pipelines zu einem kritischen Absturz-Szenario:

```
LLM Output:
"<think>
To extract the requirements, I need to define the project structure...
</think>
{
  "project_name": "stock-tracker",
  ...
}"
```

### Der Absturz (JSONDecodeError)
Wenn das Python-SDK oder eine Bibliothek wie `instructor` diesen String empfängt und versucht, ihn direkt als JSON zu parsen, stürzt die Anwendung mit einem `json.decoder.JSONDecodeError: Unexpected character: '<'` ab, da das JSON-Paket die `<think>`-Zeichen am Anfang des Strings nicht interpretieren kann.

### Drei komplementäre Engineering-Strategien zur Behebung:

#### Strategie A: Nutzung von `instructor.Mode.MD_JSON` (Empfohlen)
Durch das Umschalten des Inferenz-Modus in `instructor` auf Markdown-JSON wird das Framework angewiesen, das JSON nicht als rohen String zu erwarten, sondern gezielt nach Fenced Code Blocks (z. B. ` ```json ... ``` `) zu suchen. Da Qwen nach den `<think>`-Tags das JSON standardmäßig in solche Codeblocks einbettet, läuft das Parsing stabil durch.

#### Strategie B: Der Logit-Level GBNF-Grammar Ansatz (Für Nicht-Reasoning-Modelle)
Falls Sie ein Standard-Instruct-Modell ohne dedizierte Inferenz-Denkphase nutzen (z. B. Qwen 2.5/3.6 Instruct Standard), können Sie eine GBNF-Grammatik an `llama.cpp` übergeben. Diese zwingt das Modell auf Token-Ebene, ausschließlich gültige JSON-Syntax zu schreiben. 
* *Nachteil bei Reasoning-Modellen:* Eine GBNF-Grammatik blockiert das Modell daran, `<think>`-Tags auszugeben. Das unterdrückt die logische Denkphase des Modells, was die Codequalität drastisch reduziert!

#### Strategie C: Der Regex-Bereinigungs-Wrapper (Maximale Resilienz)
Ein robuster Custom-Wrapper in Python fängt den gesamten Text ab, protokolliert den Denkprozess (für Entwickler-Logging) und bereinigt den Payload vor der Pydantic-Validierung:

```python
import re
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def clean_and_parse_json(raw_output: str, model_schema: type[BaseModel]) -> BaseModel:
    # 1. Extrahiere den Denkprozess für Entwickler-Sichtbarkeit
    think_match = re.search(r"<think>(.*?)</think>", raw_output, re.DOTALL)
    if think_match:
        thinking_trace = think_match.group(1).strip()
        logger.info(f"--- MODEL THINKING TRACE ---\n{thinking_trace}\n----------------------------")
        # Hier optional in amadeus/logs/thinking_traces.log wegschreiben
    
    # 2. Entferne die <think>...</think> Blöcke vollständig
    clean_text = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()
    
    # 3. Falls das Modell Markdown-Codeblöcke verwendet hat, extrahiere nur deren Inhalt
    json_block = re.search(r"```json\s*(.*?)\s*```", clean_text, re.DOTALL)
    if json_block:
        clean_text = json_block.group(1).strip()
    elif clean_text.startswith("```"):
        # Catch-all für nicht-spezifizierte Codeblocks
        clean_text = re.sub(r"```[a-zA-Z]*\n|```", "", clean_text).strip()

    # 4. JSON laden und Pydantic-Instanziierung durchführen
    parsed_data = json.loads(clean_text)
    return model_schema(**parsed_data)
```

---

## 3. Die Code-Scaffolding Bedrohung: Code-Korruption durch `<think>` Tags

Ein oft übersehener, fataler Fehler bei der Nutzung lokaler Reasoning-Modelle betrifft das Modul `core/generator.py`. 
Wenn das LLM aufgefordert wird, den Inhalt für eine Python-Datei (z. B. `app.py`) zu generieren, und dabei im "Thinking"-Modus läuft, sieht die Antwort wie folgt aus:

```python
<think>
I need to import Flask, define the app object, and write the hello world endpoint.
</think>
from flask import Flask
app = Flask(__name__)
# ...
```

### Die Bedrohung:
Wird dieser String ohne Vorbehandlung direkt in die Zieldatei geschrieben, enthält `app.py` an erster Stelle die XML-Tags `<think>`. Beim Start der generierten Anwendung führt dies zu einem sofortigen Systemabsturz mit einem **`SyntaxError: invalid syntax`**, da Python diese Tags nicht interpretieren kann.

### Die Lösung:
Der Code-Generator *muss* zwingend einen Regex-Filter anwenden, um jegliche Inferenz-Tags vor dem Schreiben auf die Festplatte restlos zu eliminieren.

```python
def sanitize_generated_code(raw_code: str) -> str:
    # Entfernt alle Chain-of-Thought Blöcke vor dem Speichern der Datei
    sanitized = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
    
    # Entfernt eventuell generierte Markdown-Wrapper-Ticks
    if sanitized.startswith("```"):
        lines = sanitized.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        sanitized = "\n".join(lines).strip()
    return sanitized
```

---

## 4. Lokaler Runner Tuning-Guide & Der `llama-server` Reasoning-Bug

Bei der Ausführung von Qwen 3.6 über `llama.cpp` gibt es ein bekanntes Problem mit dem automatischen Chat-Template-Parser:

> [!WARNING]
> Der integrierte Inferenz-Parser von `llama-server` versucht standardmäßig, Reasoning-Tags automatisch zu erkennen und abzuspalten (optimiert für DeepSeek-R1). Bei Qwen 3.6 führt dies häufig zu **Silent Truncation** (das Modell bricht nach dem Denken ab, ohne das eigentliche Ergebnis auszugeben).

### Die korrekte Konfiguration
Deaktivieren Sie den internen Parser von `llama.cpp` komplett. Starten Sie das Modell mit der Option `--reasoning-format none`. Dadurch leitet `llama.cpp` die Denkprozesse ungefiltert im Textstrom an Python weiter, wo wir sie mit den oben gezeigten Regex-Funktionen stabil parsen können.

#### Optimierter Startbefehl für Windows (RTX 3060/4070/4080 mit CUDA):
```powershell
.\llama-server.exe `
  -m "C:\Models\Qwen3.6-27B-Instruct-Q4_K_M.gguf" `
  -c 32768 `
  -ngl 99 `
  -fa `
  --reasoning-format none `
  --prompt-cache "C:\Models\amadeus_cache.bin" `
  --prompt-cache-all
```

---

## 5. Vollständige, produktionsreife Python-Implementierungen

Im Folgenden finden Sie die vollständigen Modifikationen für die Klassen in `core/`, die sowohl Cloud-Dienste als auch die lokalen Qwen-Modelle robust bedienen.

### A. Core-Analyzer (`core/analyzer.py`)

```python
# c:\Users\engel\OneDrive\000000000000000000000000000000000000000 ai\AI Agents Projects\amadeus\core\analyzer.py
import os
import logging
import json
import re
import yaml
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", config_path=None, llm_provider="claude"):
        load_dotenv()
        self.llm_provider = llm_provider or "claude"
        self.model = model
        self.client = None
        self.quality_criteria = []

        # Lade lokale Inferenzkonfiguration aus config.yaml falls vorhanden
        self.local_api_base = "http://localhost:8080/v1"
        self.local_temperature = 0.1
        self.local_max_retries = 3

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    self.quality_criteria = config.get("quality_criteria", [])
                    models_cfg = config.get("models", {})
                    self.llm_provider = models_cfg.get("llm_provider", "claude")
                    
                    if self.llm_provider == "local":
                        local_cfg = models_cfg.get("local", {})
                        self.local_api_base = local_cfg.get("api_base", "http://localhost:8080/v1")
                        self.model = local_cfg.get("model_name", "qwen3.6-27b-instruct")
                        self.local_temperature = local_cfg.get("temperature", 0.1)
                        self.local_max_retries = local_cfg.get("max_retries", 3)
            except Exception as e:
                logger.error(f"Failed to load config for quality criteria: {e}")

        # Provider-Initialisierung
        if self.llm_provider == "local":
            logger.info(f"Initializing Local Instructor Client targeting: {self.local_api_base}")
            base_client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
            # MD_JSON Modus ist absolut kritisch für Qwen/DeepSeek Reasoning-Modelle
            self.client = instructor.from_openai(base_client, mode=instructor.Mode.MD_JSON)
        elif self.llm_provider == "gemini":
            import google.generativeai as genai
            self.gemini_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.gemini_key:
                logger.warning("GEMINI_API_KEY not found in environment.")
            else:
                genai.configure(api_key=self.gemini_key)
        else:
            from anthropic import Anthropic
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("Anthropic API key not found.")
            else:
                self.client = Anthropic(api_key=self.api_key)

    def _strip_thinking_tags(self, text: str) -> str:
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            logger.info(f"Detected Thinking Trace:\n{think_match.group(1).strip()}")
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def analyze(self, transcript_text):
        if not transcript_text:
            logger.error("Transcript text is empty.")
            return None

        quality_context = ""
        if self.quality_criteria:
            quality_context = "\nEnsure the generated requirements enforce the following default quality guidelines:\n" + \
                              "\n".join([f"- {criterion}" for criterion in self.quality_criteria])

        system_prompt = f"""You are a Senior Project Architect. Your job is to analyze a raw transcript of a developer describing a project they want to build. 

You must extract and organize a structured, comprehensive project specification plan. 
To do this, analyze the user's intent, resolve ambiguities, and organize the requirements into a coherent design.
{quality_context}

IMPORTANT GUIDELINES:
1. Infer additional necessary files that the developer did not explicitly mention but are essential for a complete, production-ready, clean boilerplate structure (e.g. entrypoint scripts, CLI parser, main window code, helper classes, config loader, test cases).
2. Ensure the display name is clean and the project name is filesystem-friendly (e.g., kebab-case or snake_case).
3. Ensure all files listed in `files_to_create` are essential and have specific, clear purposes.
4. If the developer mentioned specific dependencies or frameworks, include them. Also add any standard helper dependencies (e.g. python-dotenv, PyYAML, pytest).
"""

        if self.llm_provider == "local":
            logger.info("Executing local requirement extraction...")
            try:
                # Instructor führt automatisches Schema-Parsing über Pydantic durch
                requirements = self.client.chat.completions.create(
                    model=self.model,
                    response_model=RequirementsModel,
                    temperature=self.local_temperature,
                    max_retries=self.local_max_retries,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze and structure this transcript:\n\n{transcript_text}"}
                    ]
                )
                return requirements
            except Exception as e:
                logger.error(f"Instructor local analysis failed: {e}")
                # Fallback: Versuche rohe Textgenerierung und manuelle Bereinigung
                return self._fallback_manual_parse(transcript_text, system_prompt)

        elif self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                self.gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
                if not self.gemini_key:
                    logger.error("Cannot analyze: GEMINI_API_KEY is missing.")
                    return None
                genai.configure(api_key=self.gemini_key)

                logger.info("Sending transcript to Gemini for requirements extraction...")
                model_inst = genai.GenerativeModel(self.model)
                prompt = f"{system_prompt}\n\nHere is the raw audio transcript of the project description:\n\n{transcript_text}"
                
                response = model_inst.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": RequirementsModel
                    }
                )
                
                data = json.loads(response.text)
                return RequirementsModel(**data)
            except Exception as e:
                logger.error(f"Error during Gemini API analysis: {e}")
                return None

        # Claude API Logic
        if not self.client:
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.error("Cannot analyze: Anthropic API key is missing.")
                return None
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)

        logger.info("Sending transcript to Claude for requirements extraction...")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here is the raw audio transcript of the project description:\n\n{transcript_text}"}
                ],
                tools=[
                    {
                        "name": "save_requirements",
                        "description": "Saves the extracted structured project requirements.",
                        "input_schema": RequirementsModel.model_json_schema()
                    }
                ],
                tool_choice={"type": "tool", "name": "save_requirements"}
            )

            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "save_requirements":
                    tool_use_block = block
                    break

            if not tool_use_block:
                logger.error("Claude did not use the tool as requested.")
                return None

            requirements_data = tool_use_block.input
            return RequirementsModel(**requirements_data)

        except Exception as e:
            logger.error(f"Error during Claude API analysis: {e}")
            return None

    def _fallback_manual_parse(self, transcript_text, system_prompt):
        logger.info("Starting manual extraction fallback (regex)...")
        try:
            raw_client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
            response = raw_client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nReturn strictly the final JSON inside a ```json``` code block."},
                    {"role": "user", "content": transcript_text}
                ]
            )
            raw_text = response.choices[0].message.content
            cleaned_json = self._strip_thinking_tags(raw_text)
            
            # Markdown Block extrahieren
            json_block = re.search(r"```json\s*(.*?)\s*```", cleaned_json, re.DOTALL)
            if json_block:
                cleaned_json = json_block.group(1).strip()
            
            data = json.loads(cleaned_json)
            return RequirementsModel(**data)
        except Exception as ex:
            logger.critical(f"Critical failure: Both Instructor and Manual Fallback failed. {ex}")
            return None
```

---

### B. Core-Generator (`core/generator.py`)

```python
# c:\Users\engel\OneDrive\000000000000000000000000000000000000000 ai\AI Agents Projects\amadeus\core\generator.py
import os
import logging
import yaml
import re
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel
from speech_to_code.models.project import ProjectFileModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ProjectGenerator:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", llm_provider="claude", config_path=None):
        load_dotenv()
        self.llm_provider = llm_provider or "claude"
        self.model = model
        self.client = None
        
        self.local_api_base = "http://localhost:8080/v1"
        self.local_temperature = 0.2

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    models_cfg = config.get("models", {})
                    self.llm_provider = models_cfg.get("llm_provider", "claude")
                    
                    if self.llm_provider == "local":
                        local_cfg = models_cfg.get("local", {})
                        self.local_api_base = local_cfg.get("api_base", "http://localhost:8080/v1")
                        self.model = local_cfg.get("model_name", "qwen3.6-27b-instruct")
                        self.local_temperature = local_cfg.get("temperature", 0.2)
            except Exception as e:
                logger.error(f"Failed to load config in Generator: {e}")

        # Initialize clients
        if self.llm_provider == "local":
            logger.info(f"Initializing standard OpenAI client for local code generation at: {self.local_api_base}")
            self.client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
        elif self.llm_provider == "gemini":
            import google.generativeai as genai
            self.gemini_key = api_key or os.getenv("GEMINI_API_KEY")
            if self.gemini_key:
                genai.configure(api_key=self.gemini_key)
        else:
            from anthropic import Anthropic
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if self.api_key:
                self.client = Anthropic(api_key=self.api_key)

        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _sanitize_generated_code(self, raw_code: str) -> str:
        # ABSOLUT KRITISCH: Entfernt alle <think>...</think> XML-Blöcke
        # Verhindert SyntaxError in generierten Projekten
        clean_code = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
        
        # Entfernt eventuell generierte Markdown-Hüllen
        if clean_code.startswith("```"):
            lines = clean_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_code = "\n".join(lines).strip()
        return clean_code

    def generate_file_content(self, requirements: RequirementsModel, target_file_path, file_purpose):
        logger.info(f"Generating content for file: {target_file_path}...")

        files_roadmap = "\n".join([f"- `{f.file_path}`: {f.purpose}" for f in requirements.files_to_create])
        specifications_list = "\n".join([f"- {spec}" for spec in requirements.specifications])
        quality_criteria_list = "\n".join([f"- {qc}" for qc in requirements.quality_criteria])
        tech_stack_list = ", ".join(requirements.tech_stack)
        dependencies_list = ", ".join(requirements.dependencies)

        system_prompt = f"""You are an Expert Lead Software Engineer. Your task is to write the complete, high-quality, production-ready file contents for a specific file in a new project.

PROJECT DETAILS:
- Name: {requirements.display_name}
- Short Description: {requirements.short_description}
- Project Type: {requirements.project_type}
- Tech Stack: {tech_stack_list}
- Required Dependencies: {dependencies_list}

PROJECT ROADMAP / DIRECTORY STRUCTURE:
{files_roadmap}

FUNCTIONAL SPECIFICATIONS:
{specifications_list}

CODE QUALITY GUIDELINES:
{quality_criteria_list}

YOUR TASK:
Generate the contents for the file: `{target_file_path}`
File Purpose: {file_purpose}

IMPORTANT INSTRUCTIONS:
1. Provide the complete code or text for the file. Do not use placeholders, comments like "// todo implement", or truncate the output.
2. The code must compile and run cleanly, matching the project guidelines and interacting correctly with other files in the roadmap.
3. OUTPUT ONLY the direct file contents. Do NOT wrap the file contents in markdown code block ticks (like ```python or ```) under any circumstances. Start directly with imports or code. Do not include any conversational preamble or postscript.
"""

        if self.llm_provider == "local":
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.local_temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Please generate the complete, ready-to-use contents for `{target_file_path}`."}
                    ]
                )
                raw_content = response.choices[0].message.content.strip()
                return self._sanitize_generated_code(raw_content)
            except Exception as e:
                logger.error(f"Error generating content via Local AI for {target_file_path}: {e}")
                return ""

        elif self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                model_inst = genai.GenerativeModel(self.model)
                prompt = f"{system_prompt}\n\nPlease generate the complete, ready-to-use contents for `{target_file_path}`."
                response = model_inst.generate_content(prompt)
                return self._sanitize_generated_code(response.text.strip())
            except Exception as e:
                logger.error(f"Error generating content via Gemini: {e}")
                return ""

        # Claude API Logic
        if not self.client:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Please generate the complete, ready-to-use contents for `{target_file_path}`."}
                ]
            )
            content = response.content[0].text.strip()
            return self._sanitize_generated_code(content)
        except Exception as e:
            logger.error(f"Error generating content via Claude: {e}")
            return ""

    # (Verbleibende Funktionen generate_all_files und Hilfsmethoden bleiben identisch)
```

---

## 6. Zusammenfassendes Fazit & Implementierungs-Sicherheit

Durch die Implementierung der **`speech_to_code` Verzeichnis-Junction** wurden sämtliche absolute Importpfade repariert, ohne den Code anfällig für Inkompatibilitäten zu machen. 

Mit dem Wechsel zu einem lokalen Reasoning-Modell wie **Qwen 3.6** löst diese Blueprint die beiden schwerwiegendsten Systemrisiken:
1. **JSONDecodeError-Vermeidung:** Vollautomatisch über den `instructor.Mode.MD_JSON`-Standard und den robusten Regex-Sicherheits-Wrapper.
2. **Dateikorruptions-Schutz:** Durch den proaktiven Regex-Sanitizer im Code-Generator werden alle Chain-of-Thought-Traces vor dem Schreiben auf die Festplatte restlos abgefangen, um einen reibungslosen Kompiliervorgang und fehlerfreie Testläufe zu garantieren.
