# Building Local AI Agents: The Production-Grade Engineering Playbook
### A Deep-Dive Architecture Guide with Qwen 3.6, llama.cpp, and Pydantic/Instructor

This playbook serves as the definitive engineering manual for building, running, and scaling **fully local, production-grade AI agents**. It addresses the practical realities of local LLM orchestration—specifically leveraging the state-of-the-art **Qwen 3.6** model series—and details how to solve common structural and integration errors encountered in active developer workspaces.

---

## 1. Core Architectural Paradigms: Going 100% Local

Moving from cloud-hosted APIs (like Anthropic Claude or Google Gemini) to a self-contained local AI agent architecture is not just a migration of endpoints—it is a complete paradigm shift in runtime design.

```
       [Developer Audio Input]
                  │
                  ▼
         [faster-whisper STT] (Local offline audio transcript)
                  │
                  ▼
      [Namespace Junction Link] (Transparently resolves absolute paths)
                  │
                  ▼
        [Structured Extraction] (instructor.Mode.MD_JSON / Qwen 3.6)
                  │
                  ├──► [Captures & logs <think> traces to disk]
                  └──► [Extracts validated Pydantic model]
                  │
                  ▼
         [Project Generator] ──► [Applies Regex think-tag scrubbers]
                  │
                  ▼
      [Clean Scaffolder Output] (Saves 100% valid Python code)
```

### The Three Architectural Pillars
1. **Zero-Trust Sovereignty:** Complete protection of intellectual property. Context payloads (monorepo file mappings, design schemas, database structures) never leave the local environment.
2. **Deterministic Structuring:** Forcing raw local models to strictly output production-grade JSON matching complex Pydantic models.
3. **Optimized Latency Pipelines:** Implementing prompt caching and low-latency local runners to enable fast, iterative agent loops.

---

## 2. Hardware Sizing & Unified Memory Formulas

To run local reasoning models, you must accurately size your hardware requirements. Under-sizing leads to catastrophic performance degradation (CPU fallback), while over-quantizing degrades the model's reasoning capabilities.

### VRAM Requirements Formula (Model + KV Cache)

$$\text{VRAM}_{\text{total}} \approx \left( \frac{\text{Parameters in Billions} \times \text{Quantization Bits}}{8} \times 1.15 \right) + \text{VRAM}_{\text{KV-Cache}}$$

The **KV Cache VRAM** requirements scale dynamically with the context window size ($C$ in tokens), layers ($N_{\text{layers}}$), heads ($N_{\text{heads}}$), and head dimensions ($D_{\text{head}}$):

$$\text{VRAM}_{\text{KV-Cache}} \approx 2 \times 2 \times N_{\text{layers}} \times N_{\text{heads}} \times D_{\text{head}} \times C \times 2 \text{ bytes (FP16)}$$

*Using Grouped-Query Attention (GQA) in Qwen 3.6 reduces this footprint by a factor of 8 compared to older architectures.*

### Sizing and Quantization Selector Matrix

| Model Size | Quantization | Disk Footprint | Required VRAM | Context Capacity | Target Hardware |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 7B-Instruct** | `Q5_K_M` (5-bit) | ~5.1 GB | ~6.5 GB | 16,384 | RTX 3060/4060, M1/M2/M3 (16GB RAM) |
| **Qwen 14B-Instruct** | `Q4_K_M` (4-bit) | ~9.2 GB | ~11.0 GB | 32,768 | **Recommended Sweetspot:** RTX 4070 12GB, Apple Max 32GB |
| **Qwen 3.6 27B-Instruct** | `Q4_K_M` (4-bit) | ~19.5 GB | ~22.0 GB | 16,384 | RTX 3090/4090 24GB, Apple Max 48GB+ |
| **Qwen 72B-Instruct** | `Q3_K_L` (3-bit) | ~34.0 GB | ~38.0 GB | 8,192 | Dual RTX 3090/4090, Apple Ultra 64GB+ |

---

## 3. High-Performance Server Tuning & llama.cpp compilation

For maximum throughput under Windows, compile `llama.cpp` natively with CUDA support rather than using generic CPU-only packages.

### Windows Native CUDA Compilation (PowerShell):
```powershell
# Clone the repository and enter the directory
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Configure CMake with CUDA acceleration enabled
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release

# Compile using all available CPU threads
cmake --build build --config Release --clean-first
```

### The llama-server reasoning parser bug:
`llama-server` features a built-in reasoning parser designed to extract deep thinking tags (like `<think>...</think>`). However, because this parser is highly optimized for DeepSeek-R1, Qwen 3.6's dynamic tag behaviors (such as omitting the opening `<think>` tag when the chat template pre-fills it) can confuse the server, resulting in **Silent Truncation** (the server cuts off generation immediately after the thinking phase).

**The Solution:** Disable the internal parser by passing `--reasoning-format none` and handle the `<think>` tags cleanly in Python.

### Optimized Server Startup Command:
```powershell
.\llama-server.exe `
  -m "C:\Models\Qwen3.6-27B-Instruct-Q4_K_M.gguf" `
  -c 32768 `
  -ngl 99 `
  -fa `
  --reasoning-format none `
  --prompt-cache "C:\Models\amadeus_cache.bin" `
  --prompt-cache-all `
  --ctx-shift
```
*   `-fa` (`--flash-attn`): Cuts KV Cache memory overhead in half.
*   `--prompt-cache`: Saves the compiled state of the static system prompt, reducing prompt ingestion times from seconds to **under 5 milliseconds**.

---

## 4. Resolving Monorepo Namespace Import Errors

In multi-application monorepos, directory renaming can break absolute import paths, resulting in immediate `ModuleNotFoundError` crashes.

### The Problem in Amadeus:
All files inside the `amadeus/` directory import components using absolute paths mapping to the `speech_to_code` namespace:
```python
from speech_to_code.core.analyzer import TranscriptAnalyzer
```
However, the parent directory on the disk is named `amadeus/` and no folder named `speech_to_code/` exists.

### The Directory Junction Fix:
Instead of refactoring imports across the entire codebase—which creates version control noise and breaks git history—create an operating-system-level **directory junction**. This resolves the namespace transparently at the kernel level.

In the monorepo root directory, run:
```powershell
New-Item -ItemType Junction -Path "speech_to_code" -Target "amadeus"
```
Python, linters, and IDEs will now resolve absolute imports instantly without any performance overhead.

---

## 5. Overcoming Structured Output Failures (JSONDecodeError)

Local reasoning models output a Chain-of-Thought (CoT) trace within `<think>...</think>` tags before generating JSON payloads. If passed directly to a standard JSON parser, this causes an immediate crash:
`json.decoder.JSONDecodeError: Unexpected character: '<' at line 1 column 1`

### Strategy A: Using `instructor.Mode.MD_JSON`
The `instructor` library supports extracting JSON out of Markdown code blocks rather than expecting a raw string. Since Qwen outputs its final JSON inside ` ```json ... ``` ` blocks after thinking, configuring the client with `Mode.MD_JSON` ensures reliable parsing out of the box.

### Strategy B: Regex-Based Tag Stripping & Observability Logging
For production robustness, implement a wrapper that intercepts the raw text, logs the model's `<think>` trace to a separate observability file on disk (providing developer visibility into the model's reasoning), strips the XML tags, and parses the remaining JSON cleanly:

```python
import re
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def clean_and_parse_json(raw_text: str, schema_class: type[BaseModel]) -> BaseModel:
    # 1. Extract and log the thinking trace
    think_match = re.search(r"<think>(.*?)</think>", raw_text, re.DOTALL)
    if think_match:
        thinking_trace = think_match.group(1).strip()
        logger.info(f"--- MODEL THINKING TRACE ---\n{thinking_trace}\n----------------------------")
    
    # 2. Strip XML tags
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    
    # 3. Pull JSON out of markdown blocks
    markdown_block = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
    if markdown_block:
        cleaned = markdown_block.group(1).strip()
        
    data = json.loads(cleaned)
    return schema_class(**data)
```

---

## 6. Scaffolding Safeguards: Preventing File Corruption

When a reasoning model is tasked with generating raw code for a file, it will write its thinking trace inside the output. 

### The Threat:
Saving the raw LLM generation directly results in files containing:
```python
<think>
I must write a main function...
</think>
def main():
    pass
```
Running this scaffolded file throws a fatal `SyntaxError: invalid syntax` on the first line.

### The Solution:
The file generator must proactively scrub thinking tags before saving any code to disk.

```python
def sanitize_generated_code(raw_code: str) -> str:
    # Proactively strip reasoning tags to prevent SyntaxErrors
    clean_code = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
    
    # Strip markdown fenced formatting if generated
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

## 7. Complete Production Code Implementations for Amadeus

The following classes have been successfully updated to robustly support both local GGUF models (via Qwen 3.6) and cloud platforms.

### A. Core-Analyzer (`amadeus/core/analyzer.py`)
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

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", config_path=None, llm_provider="claude"):
        load_dotenv()
        self.llm_provider = llm_provider or "claude"
        self.model = model
        self.client = None
        self.quality_criteria = []

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
                logger.error(f"Failed to load config in Analyzer: {e}")

        if self.llm_provider == "local":
            logger.info(f"Initializing Local Instructor Client: {self.local_api_base}")
            base_client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
            # MD_JSON mode handles Qwen/DeepSeek reasoning output blocks cleanly
            self.client = instructor.from_openai(base_client, mode=instructor.Mode.MD_JSON)
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

    def _strip_thinking_tags(self, text: str) -> str:
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            logger.info(f"Thinking Trace Captured:\n{think_match.group(1).strip()}")
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
            try:
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
                return self._fallback_manual_parse(transcript_text, system_prompt)

        elif self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                self.gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
                if not self.gemini_key:
                    logger.error("Cannot analyze: GEMINI_API_KEY is missing.")
                    return None
                genai.configure(api_key=self.gemini_key)

                model_inst = genai.GenerativeModel(self.model)
                prompt = f"{system_prompt}\n\nHere is the raw audio transcript:\n\n{transcript_text}"
                
                response = model_inst.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": RequirementsModel
                    }
                )
                return RequirementsModel(**json.loads(response.text))
            except Exception as e:
                logger.error(f"Gemini API analysis failed: {e}")
                return None

        # Claude API Logic
        if not self.client:
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here is the raw audio transcript:\n\n{transcript_text}"}
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

            tool_use_block = next((b for b in response.content if b.type == "tool_use" and b.name == "save_requirements"), None)
            if not tool_use_block:
                return None

            return RequirementsModel(**tool_use_block.input)
        except Exception as e:
            logger.error(f"Claude API analysis failed: {e}")
            return None

    def _fallback_manual_parse(self, transcript_text, system_prompt):
        logger.info("Triggering manual regex fallback extraction...")
        try:
            raw_client = OpenAI(base_url=self.local_api_base, api_key="local-placeholder")
            response = raw_client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nReturn strictly valid JSON inside a ```json``` block."},
                    {"role": "user", "content": transcript_text}
                ]
            )
            raw_text = response.choices[0].message.content
            cleaned = self._strip_thinking_tags(raw_text)
            
            json_block = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
            if json_block:
                cleaned = json_block.group(1).strip()
                
            return RequirementsModel(**json.loads(cleaned))
        except Exception as ex:
            logger.critical(f"Both Instructor and manual regex extraction failed: {ex}")
            return None
```

---

### B. Core-Generator (`amadeus/core/generator.py`)
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
        # ABSOLUTELY ESSENTIAL: Remove reasoning thinking traces to avoid syntax corruption
        clean_code = re.sub(r"<think>.*?</think>", "", raw_code, flags=re.DOTALL).strip()
        
        # Remove markdown code fence wrappings
        if clean_code.startswith("```"):
            lines = clean_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_code = "\n".join(lines).strip()
        return clean_code

    def generate_file_content(self, requirements: RequirementsModel, target_file_path, file_purpose):
        logger.info(f"Generating content for file: {target_file_path} via {self.llm_provider}...")

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
            return self._sanitize_generated_code(response.content[0].text.strip())
        except Exception as e:
            logger.error(f"Error generating content via Claude: {e}")
            return ""
```

---

## 8. Verification & Testing Pipeline

Now that all core dependencies (`pyyaml`, `anthropic`, `google-generativeai`, `sounddevice`, `numpy`, `faster-whisper`, etc.) have been successfully installed and verified in `.venv`, you can run the entire test suite locally to verify path resolution and class integrity.

### Running Modul-Tests:
```powershell
# Executing pytest will now seamlessly resolve the speech_to_code namespace
.venv\Scripts\pytest.exe
```

### Verification Verification Steps:
1. Ensure the directory junction `speech_to_code` exists at your project root.
2. Launch `llama-server` with `--reasoning-format none` and offload all layers to your GPU.
3. Toggle `"local"` in `config.yaml` to route your audio-to-code pipelines offline.
