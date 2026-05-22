# Local AI Integration Plan: Qwen 3.6 for Amadeus

Dieses Dokument hält die Strategie und Architektur-Entscheidungen für die Migration von Amadeus auf einen **lokalen, datenschutzfreundlichen AI-Stack** mit **Qwen 3.6** fest.

---

## 1. Warum Qwen 3.6?
- **Souveränität:** 100% lokale Ausführung – sensible Projektkontexte und Dokumente verlassen nie die lokale Maschine.
- **Riesiger Kontext:** Bis zu 1 Million Token (Qwen 3.6 Plus) ermöglicht das Laden ganzer Workspaces ohne Truncation.
- **Agentic Coding Focus:** Die Baureihe ist speziell für Repository-Reasoning und strukturiertes Arbeiten optimiert.

---

## 2. Ausführung OHNE Ollama (Direkter Download & alternative Runner)

Es ist **nicht** zwingend erforderlich, Ollama zu nutzen. Qwen 3.6 (in den Open-Weights-Varianten wie `Qwen3.6-27B` oder `Qwen3.6-35B-A3B`) kann direkt bezogen und über verschiedene Wege ausgeführt werden:

### Download-Quellen & Bezugsdaten
- **Hugging Face (Standard-Quelle):** Die primäre Plattform für Open-Source LLMs. 
  - *Suchbegriffe:* Suche auf [huggingface.co](https://huggingface.co/) nach `Qwen/Qwen3.6-27B-Instruct-GGUF` (offizielle Versionen) oder Community-Builds von Erstellern wie `Bartowski` (z. B. `Bartowski/Qwen3.6-27B-Instruct-GGUF`).
  - *Auswahl:* Unter *Files and versions* die `.gguf`-Datei herunterladen (Empfehlung: `Q4_K_M` oder `Q5_K_M` für das beste Verhältnis von Qualität zu VRAM).
- **LM Studio In-App-Suche (Einfachste Methode):** 
  - Direkt im Suchfeld in LM Studio nach `Qwen 3.6` suchen. Das Tool listet die passenden GGUF-Modelle von Hugging Face auf und lädt sie per Ein-Klick-Download direkt in das richtige Verzeichnis.
- **ModelScope (Alternative):** 
  - Alibabas eigene Open-Source-Plattform. Dient als Ausweich-Mirror, falls Hugging Face eine eingeschränkte Bandbreite aufweist.

---

### A. LM Studio (Die einfachste Desktop-Alternative)
1. **Suche & Download:** In LM Studio nach `Qwen 3.6 GGUF` suchen.
2. **Quantisierung wählen:** Eine passende Quantisierung (z. B. `Q4_K_M` oder `Q5_K_M` für ein optimales Verhältnis zwischen Qualität und VRAM-Bedarf) herunterladen.
3. **Local Server:** Über den Server-Tab in LM Studio mit einem Klick einen lokalen, OpenAI-kompatiblen Server auf `http://localhost:1234/v1` starten.

### B. llama.cpp (Maximale Performance & minimaler Overhead)
1. **Download:** Die GGUF-Dateien direkt von Hugging Face herunterladen (z. B. vom Repository `Bartowski` oder `Qwen`).
2. **Server starten:** `llama.cpp` kompilieren oder die Binaries herunterladen und den Server per Terminal starten:
   ```bash
   ./llama-server -m path/to/qwen3.6-27b-q4_k_m.gguf -c 16384 --port 8080
   ```
   *Hinweis:* `-c 16384` definiert das Kontextfenster (kann je nach Hardware und VRAM bis auf 128k+ erhöht werden).

### C. Jan.ai (Open-Source Desktop GUI)
- Ähnlich wie LM Studio, eine minimalistische Open-Source-Alternative, die ebenfalls einen lokalen OpenAI-kompatiblen API-Server anbietet.

---

## 3. Geplante Code-Anpassungen in Amadeus

Um den lokalen AI-Support zu aktivieren, müssen folgende Änderungen vorgenommen werden:

### A. Konfiguration in `amadeus/config.yaml`
```yaml
models:
  llm_provider: "local"
  local:
    api_base: "http://localhost:1234/v1"   # LM Studio Default
    model_name: "qwen3.6-27b-instruct"    # Name des geladenen GGUF-Modells
```

### B. Schnittstellen-Abstraktion in Python
Die Dateien `core/analyzer.py`, `core/generator.py` und `core/validator.py` greifen über das `openai`-Bibliothek-SDK auf die lokale Schnittstelle zu. Da LM Studio und `llama.cpp` das OpenAI-Format voll unterstützen, reicht folgende Initialisierung:

```python
from openai import OpenAI

class TranscriptAnalyzer:
    def __init__(self, config):
        if config.llm_provider == "local":
            self.client = OpenAI(
                base_url=config.local.api_base,
                api_key="not-needed"  # Lokale Server ignorieren den API-Key
            )
            self.model = config.local.model_name
```

---

## 4. Wichtig für die nächste Session 💡
Dieses Konzept stellt sicher, dass Amadeus vollkommen unabhängig von teuren APIs und Drittanbieter-Services läuft. In der nächsten Session soll die `config.yaml` erweitert und die Abstraktion im Python-Code implementiert werden, um den `"local"` Provider nahtlos auszuwählen.
