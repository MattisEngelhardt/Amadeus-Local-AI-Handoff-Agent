# ARCHIVED LEGACY ORIGINAL

This file is preserved for traceability only. It is superseded by the current Amadeus architecture.
Current target: `gemma4:e4b` via Ollama, local `faster-whisper`, no required cloud LLM provider, and Amadeus as a handoff-workspace prep agent.

For the curated summary, use `../LOCAL_AI_RESEARCH_ARCHIVE.md`.

# Local LLM Agent Setup — Entscheidungsdokumentation

> **Hardware:** ASUS Vivobook Pro 16 OLED K6604JV · i9-13980HX · RTX 4060 (8GB VRAM) · 32GB DDR5 RAM (fest verlötet) · 1TB SSD
> **Ziel:** Eigenen AI-Agenten bauen, der lokal läuft — kein Abo, kein Limit, Portfolio-tauglich

---

## 1. Architekturentscheidung: Lokal + Cloud Hybrid

### Warum nicht nur Cloud

| Option | Problem |
|---|---|
| Claude Code (Anthropic) | Min. $20/Monat Pro, $200/Monat Max |
| NVIDIA NIM allein | 1.000 Credits, 40 req/min — endlich |
| OpenRouter free | 50 req/day — zu wenig für Agenten-Loops |

### Warum nicht nur Lokal

8GB VRAM limitiert auf Modelle ≤ ~7B Parameter (vollständig in GPU). Größere Modelle laufen langsam über CPU-Offloading.

### Entscheidung: Hybrid

```
Lokales Modell (Ollama)     →  Haupt-Backbone, unbegrenzt, 0€
NVIDIA NIM (Cloud)          →  komplexe Tasks, große Modelle
```

**Begründung:** Kein dauerhaftes Limit lokal. Cloud nur für das was lokal nicht reicht. Für Portfolio zeigt das Architektur-Denken statt blindes API-Konsumieren.

---

## 2. Modellentscheidung: Gemma 4 E4B

### Warum Gemma 4 E4B und nicht Qwen3 14B

Qwen3 14B war die erste Empfehlung. Nach Deep Research in der Community (r/LocalLLaMA, gemma4-ai.com, April/Mai 2026) hat sich das Bild verschoben:

**Gemma 4 E4B** — released 2. April 2026, Google DeepMind — ist eine MoE-Architektur (Mixture of Experts):
- 26B Parameter total, nur **~4B aktiv pro Token**
- Ergebnis: 26B-Qualität bei 4B-VRAM-Kosten

| Benchmark | Gemma 4 E4B | Gemma 3 27B |
|---|---|---|
| HumanEval (Coding) | **80%** | 29% |
| Codeforces ELO | 2150 | — |
| LiveCodeBench v6 | 80% | — |
| VRAM nötig (Q4_K_M) | **~5GB** | ~16GB |

> Quelle: Google DeepMind release notes, gemma4-ai.com (April 2026), dev.to community benchmarks

**Gemma 4 E4B schlägt Gemma 3 27B auf Coding-Tasks während es 6x weniger VRAM braucht.**

### Warum nicht Qwen3 8B / 14B

- Qwen3 8B: schwächer als Gemma 4 E4B auf Coding
- Qwen3 14B: braucht 8GB VRAM + RAM-Offloading → langsamer, kein vollständiger GPU-Run
- Gemma 4 E4B: komplett in 8GB VRAM, maximale GPU-Auslastung (70–90%)

### Hardware-Verifikation

> Quelle: databasemart.com RTX 4060 Ollama Benchmark

Modelle unter 5GB auf RTX 4060 mit Q4-Quantisierung: **40–52 Tokens/Sekunde**
Gemma 4 E4B (Q4_K_M) = ~5GB → passt komplett in 8GB VRAM → ~40–50 tok/s

---

## 3. Inference-Engine-Entscheidung: Ollama

### Vergleich der drei Optionen

| | Ollama | LM Studio | llama.cpp |
|---|---|---|---|
| Speed vs. LM Studio | ✅ **25% schneller** | Baseline | ✅✅ max (komplex) |
| Setup | `ollama pull gemma4:e4b` | GUI | selbst kompilieren |
| OpenAI-kompat. API | ✅ sofort auf :11434 | ✅ möglich | manuell |
| Agenten-Integration | ✅ direkt | ⚠️ overhead | ❌ frickelei |
| Docker/CI-fähig | ✅ | ❌ | ⚠️ |

> Quelle: Direkter Benchmark Gemma 4 E4B Ollama vs. LM Studio, Medium (rviragh, April 2026) — Ollama 25% schneller bei gleicher Quantisierung

**llama.cpp** nur sinnvoll wenn maximale Inferenz-Performance kritisch ist und man CUDA-Kompilierung selbst machen will. Für einen Agenten unnötiger Overhead.

**Entscheidung: Ollama**

---

## 4. Cloud-Fallback: NVIDIA NIM

Für Tasks die Gemma 4 E4B lokal überfordern (komplexe Reasoning-Chains, sehr große Codebases):

| Provider | Modell | Gratis? | Limit |
|---|---|---|---|
| **NVIDIA NIM** | Qwen3 Coder 480B, MiniMax M2.7 | ✅ | 40 req/min |
| OpenRouter | DeepSeek, Llama 4 | ✅ (free models) | 50 req/day |
| Groq | Llama 3.3 70B | ✅ | RPM-basiert |

> Quelle: build.nvidia.com, aitoolsmentor.com (Mai 2026) — 46+ kostenlose Modelle, kein Kreditkarte

**NIM-Vorteil:** Dieselbe OpenAI-kompatible API wie Ollama. Nur `base_url` tauschen:

```python
# Lokal (Ollama)
base_url = "http://localhost:11434/v1"

# Cloud (NVIDIA NIM)
base_url = "https://integrate.api.nvidia.com/v1"
```

---

## 5. Implementierung

### Setup Ollama + Gemma 4 E4B

```bash
# 1. Ollama installieren
curl -fsSL https://ollama.com/install.sh | sh

# 2. Gemma 4 E4B laden
ollama pull gemma4:e4b

# 3. Verifizieren
ollama run gemma4:e4b "Schreib eine Python-Funktion für Fibonacci"
```

### Agenten-Code (Provider-agnostisch)

```python
import os
from openai import OpenAI

# Provider per Env-Variable wählbar
PROVIDER = os.getenv("LLM_PROVIDER", "local")

PROVIDERS = {
    "local": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "gemma4:e4b"
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": os.getenv("NVIDIA_API_KEY"),
        "model": "qwen/qwen3-coder-480b"
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": "llama-3.3-70b-versatile"
    }
}

config = PROVIDERS[PROVIDER]
client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])

def run_agent(prompt: str) -> str:
    response = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content
```

```bash
# Lokal (Standard, kein Limit)
LLM_PROVIDER=local python agent.py

# Cloud für komplexe Tasks
LLM_PROVIDER=nvidia python agent.py
```

### Empfohlene Quantisierung

```bash
# Standard — beste Balance Speed/Qualität
ollama pull gemma4:e4b          # Q4_K_M, ~5GB, default

# Falls mehr Qualität nötig (5GB VRAM frei)
# Über LM Studio herunterladen: gemma-4-E4B-it-Q8_0.gguf (~8GB)
```

---

## 6. Entscheidungsbaum für den Agenten

```
Task eintreffen
│
├── Einfach / Routine / Datenschutz-sensitiv
│   └── Gemma 4 E4B lokal (Ollama) → kein Limit, sofort
│
└── Komplex / Großes Codebase / Reasoning-heavy
    └── NVIDIA NIM → Qwen3 Coder 480B → Cloud
```

---

## 7. Was das für das Portfolio bedeutet

Dieses Setup demonstriert:

- **Architektur-Denken:** Provider-agnostischer Code — ein Env-Switch, kein Refactoring
- **Infrastruktur-Verständnis:** Wissen wann lokal vs. Cloud sinnvoll ist und warum
- **Kein API-Konsument-Vibe:** Versteht Quantisierung, VRAM-Limits, Inference-Engines
- **Reproduzierbar:** Jeder kann klonen und in 2 Befehlen starten — kein "läuft nur auf meiner Maschine"

```
├── agent/
│   ├── agent.py              # Provider-agnostischer Core
│   ├── providers.py          # Local / NIM / Groq Konfiguration
│   └── tools/                # Agent-Tools
├── benchmarks/
│   └── local_vs_cloud.md     # Eigener Vergleich — zeigt Verständnis
├── .env.example              # Kein hardcoded Key
└── README.md                 # Setup in unter 5 Minuten
```

---

## 8. Quellen

| Claim | Quelle |
|---|---|
| Gemma 4 E4B 80% HumanEval | Google DeepMind release, dev.to (April 2026) |
| Ollama 25% schneller als LM Studio | medium.com/@rviragh Benchmark (April 2026) |
| RTX 4060 40–52 tok/s bei <5GB Modellen | databasemart.com RTX 4060 Ollama Benchmark |
| NVIDIA NIM 46+ kostenlose Modelle | aitoolsmentor.com (Mai 2026), build.nvidia.com |
| Gemma 4 E4B ~5GB VRAM (Q4_K_M) | gemma4-ai.com Hardware Guide (April 2026) |
| Gemma 4 E4B schlägt Gemma 3 27B | gemma4-ai.com, codersera.com (April 2026) |
| NIM 40 req/min Limit | build.nvidia.com Dokumentation |

---

*Erstellt: Mai 2026 — basierend auf Community-Research r/LocalLLaMA, gemma4-ai.com, databasemart.com, Medium*
