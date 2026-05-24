# Amadeus Documentation Cleanup Plan

Status: Planning document
Date: 2026-05-24
Goal: Turn the current Amadeus folder into a precise, contradiction-free, build-ready project workspace without losing valuable existing research.

## 1. Objective

The Amadeus folder currently contains valuable material, but it is not yet a coherent project brain. Some documents still describe older assumptions: Qwen, Claude/Gemini/OpenAI/NVIDIA providers, cloud fallback, code generation, and mixed local/cloud workflows.

The cleanup must produce a top-notch Amadeus project folder where every document has a clear role, every major decision is traceable, and the final agent instructions are strong enough for Codex, Claude Code, or Antigravity to work from.

The canonical direction is already fixed:

- `AMADEUS_WORKFLOW_BLUEPRINT.md` and `GEMMA_TO_AMADEUS_BLUEPRINT.md` are the current state-of-the-art reference documents for Amadeus.
- Every cleanup decision must align with these two documents unless the user explicitly updates the target architecture later.
- Amadeus is Gemma 4 E4B as a local prep agent.
- Runtime is local via Ollama.
- Telegram and desktop speechbar are the primary inputs.
- Voice-to-text is local and free via faster-whisper.
- Amadeus prepares context, prompts, source mappings, and handoff workspaces.
- Amadeus does not execute the final user task.
- The final workspace contract uses English file and folder names.
- `CLAUDE.md` is the brain for Claude Code.
- `AGENTS.md` is the Codex-compatible brain.

## 2. Cleanup Principles

### 2.1 Preserve Before Rewriting

Do not delete old knowledge just because it conflicts with the new architecture. First classify it:

- still canonical,
- useful but outdated,
- useful as background research,
- contradicted and should be archived,
- implementation detail to revisit later.

### 2.2 Separate Product Truth From Research

The final Amadeus folder must distinguish between:

- canonical product decisions,
- implementation plans,
- research notes,
- historical documents,
- generated templates,
- runtime configuration.

Old research can stay, but it must not appear as the current source of truth.

### 2.3 One Source Of Truth For Each Question

Every important question must have exactly one canonical home:

- What is Amadeus? -> product blueprint.
- How does the workflow run? -> workflow blueprint.
- How does Gemma become Amadeus? -> behavior/fine-tuning blueprint.
- How should future agents work in this repo? -> `AGENTS.md`.
- How should Claude Code understand the project? -> `CLAUDE.md`.
- What is already implemented vs planned? -> implementation status.

### 2.4 Do Not Overload `CLAUDE.md`

The final `CLAUDE.md` must be the brain, not a dumping ground. It should route to deeper documents with precise links.

It should contain:

- mission,
- current state,
- non-negotiable architecture decisions,
- file map,
- reading order,
- build plan,
- verification rules,
- active next steps.

It should not contain every full research note.

## 3. Planned Target Documentation Structure

Recommended final structure inside `amadeus/`:

```text
amadeus/
├── CLAUDE.md
├── AGENTS.md
├── README.md
├── PROJECT_STATUS.md
├── REQUIREMENTS.md
├── AMADEUS_WORKFLOW_BLUEPRINT.md
├── GEMMA_TO_AMADEUS_BLUEPRINT.md
├── IMPLEMENTATION_ROADMAP.md
├── DOCUMENTATION_INDEX.md
├── docs/
│   ├── research/
│   │   ├── LOCAL_AI_RESEARCH_ARCHIVE.md
│   │   └── LEGACY_QWEN_LLAMA_CPP_NOTES.md
│   ├── decisions/
│   │   └── ARCHITECTURE_DECISIONS.md
│   └── templates/
│       ├── TARGET_CLAUDE_TEMPLATE.md
│       └── TARGET_AGENTS_TEMPLATE.md
├── templates/
├── core/
├── models/
├── tests/
└── ui/
```

This structure keeps the root small and useful while preserving deeper research.

## 4. Document Roles After Cleanup

### 4.1 `CLAUDE.md`

Purpose: Claude Code entrypoint and state machine for the Amadeus project itself.

Must include:

- role alignment,
- current mission,
- hard constraints,
- status overview,
- semantic file map,
- precise reading order,
- links to canonical blueprints,
- implementation phases,
- verification checklist,
- rules for changing docs and code.

### 4.2 `AGENTS.md`

Purpose: Codex-compatible working instructions for this repository.

Must include:

- concise project rules,
- file ownership map,
- current source-of-truth list,
- no-cloud-provider constraint for Amadeus,
- expected commands,
- testing expectations,
- edit discipline,
- next implementation priorities.

### 4.3 `README.md`

Purpose: human-facing project overview.

Must be rewritten to match the new architecture:

- Amadeus is local Gemma E4B prep agent.
- Telegram and desktop speechbar input.
- local faster-whisper transcription.
- final handoff workspace.
- no cloud provider as default.

### 4.4 `REQUIREMENTS.md`

Purpose: canonical product requirements.

Keep and refine:

- problem statement,
- context collection phase,
- work phase,
- folder generation,
- master `CLAUDE.md` anatomy.

Remove or rewrite:

- OpenAI Whisper API as default,
- DeepSeek/Anthropic/Groq as synthesis providers,
- any implication that cloud fallback is part of core.

### 4.5 `AMADEUS_WORKFLOW_BLUEPRINT.md`

Purpose: canonical detailed workflow.

Keep as source of truth for:

- Telegram input,
- desktop speechbar,
- transcription,
- prompt compiler,
- gap analysis,
- readiness gate,
- workspace build,
- handoff.

### 4.6 `GEMMA_TO_AMADEUS_BLUEPRINT.md`

Purpose: canonical behavior architecture.

Keep as source of truth for:

- Modelfile,
- Agent Constitution,
- behavioral modes,
- skills,
- tool rituals,
- structured outputs,
- memory,
- validation,
- evals,
- later LoRA/QLoRA/DPO.

### 4.7 `LOCAL_AI_PLAN.md`

Purpose after cleanup: archive or condensed research note.

Action:

- remove as canonical architecture document,
- extract any still-useful local-agent patterns,
- move outdated Qwen/llama.cpp/cloud-fallback content into research archive,
- add a top warning that it is superseded by the two new blueprints.

### 4.8 `LOCAL_AI_AGENT_MASTERCLASS.md`

Purpose after cleanup: legacy research archive.

Action:

- preserve useful lessons about structured outputs, reasoning-tag cleanup, and validator patterns,
- mark Qwen-specific, Claude/Gemini-specific, and code-generator-specific sections as legacy,
- move or rewrite into `docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md`.

### 4.9 Root-level `local-llm-agent-setup.md`

Purpose after cleanup: integrate or retire.

Action:

- move relevant Gemma/Ollama notes into Amadeus docs,
- remove NVIDIA/Groq/OpenRouter provider switch as canonical design,
- mark as superseded or relocate into `docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md`.

### 4.10 `config.yaml`

Purpose: runtime configuration.

Must be updated later during implementation, not during documentation cleanup unless explicitly approved.

Target direction:

```yaml
models:
  llm_provider: "local"
  local:
    runtime: "ollama"
    model_name: "gemma4:e4b"
    api_base: "http://localhost:11434/v1"
  transcription:
    provider: "faster-whisper"
    model_name: "large-v3"
    language: "de"
```

### 4.11 `requirements.txt`

Purpose: Python dependencies.

Should eventually remove unused cloud dependencies if the code no longer needs them.

Do not change until code architecture is changed.

## 5. Audit Procedure Before Editing

The cleanup should start with a documentation inventory:

1. List all text-like files in `amadeus/`.
2. Classify each as canonical, implementation, template, research, legacy, config, or generated.
3. For every Markdown document, identify:
   - main purpose,
   - current useful content,
   - contradictions,
   - duplicate sections,
   - target destination.
4. Compare every provider/model reference against the canonical decision:
   - allowed: Gemma 4 E4B, Ollama, faster-whisper.
   - contextual only: Codex, Claude Code, Antigravity as later execution environments.
   - legacy only: Qwen, llama.cpp, Gemini, OpenAI API, Anthropic, Groq, NVIDIA.
5. Do not edit until the classification matrix is reviewed.

## 6. Proposed Cleanup Phases

### Phase 1: Documentation Inventory

Deliverable:

```text
DOCUMENTATION_INDEX.md
```

Content:

- every relevant document,
- role,
- status,
- whether canonical,
- what it links to,
- what should happen to it.

### Phase 2: Canonical Root Docs

Deliverables:

```text
CLAUDE.md
AGENTS.md
README.md
PROJECT_STATUS.md
```

Goal:

Make it impossible for a future agent to misunderstand the Amadeus direction.

### Phase 3: Requirements Rewrite

Deliverable:

```text
REQUIREMENTS.md
```

Goal:

Turn the existing strong conceptual material into a clean product requirements document aligned with the new workflow.

### Phase 4: Research Archive

Deliverables:

```text
docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md
docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md
```

Goal:

Preserve old thinking without letting it remain current architecture.

### Phase 5: Implementation Roadmap

Deliverable:

```text
IMPLEMENTATION_ROADMAP.md
```

Goal:

Translate the blueprints into build phases:

1. Ollama/Gemma harness.
2. Telegram ingestion.
3. faster-whisper transcription.
4. project state store.
5. prompt compiler.
6. gap analysis.
7. document processing.
8. workspace builder.
9. `CLAUDE.md` / `AGENTS.md` generator.
10. validation and eval suite.

### Phase 6: Template System

Deliverables:

```text
docs/templates/TARGET_CLAUDE_TEMPLATE.md
docs/templates/TARGET_AGENTS_TEMPLATE.md
templates/
```

Goal:

Avoid relying on Gemma to invent perfect structures from scratch.

### Phase 7: Final Consistency Audit

Deliverable:

```text
PROJECT_STATUS.md
```

Checklist:

- no current doc presents Qwen as target model,
- no current doc presents cloud API as required provider,
- no current doc presents Amadeus as final task executor,
- every root doc links to the canonical blueprints,
- every archived doc is clearly marked as legacy,
- `CLAUDE.md` and `AGENTS.md` provide clear agent instructions.

## 7. Final `CLAUDE.md` Design

The final `CLAUDE.md` for Amadeus should follow the ten-pillar pattern from `REQUIREMENTS.md`.

Recommended sections:

```md
# Amadeus Project Brain

## 1. Role Alignment
You are working on Amadeus, a local Gemma 4 E4B prep agent.

## 2. Non-Negotiable Constraints
- No cloud LLM provider in the core workflow.
- Core model is gemma4:e4b via Ollama.
- Amadeus prepares handoff workspaces; it does not execute final user projects.

## 3. Current Project State
- Documentation cleanup in progress.
- Canonical blueprints exist.
- Implementation still reflects older provider assumptions.

## 4. Canonical Reading Order
1. AMADEUS_WORKFLOW_BLUEPRINT.md
2. GEMMA_TO_AMADEUS_BLUEPRINT.md
3. REQUIREMENTS.md
4. IMPLEMENTATION_ROADMAP.md
5. PROJECT_STATUS.md

## 5. Semantic File Map
Explain each key file and when to use it.

## 6. Architecture Decisions
Link to decisions and summarize the current choices.

## 7. Work Rules
How agents should edit, validate, and avoid reviving legacy assumptions.

## 8. Quality Rubric
What counts as a correct Amadeus change.

## 9. Micro-Workflows
Before editing docs, classify.
Before changing code, check current docs.
Before adding providers, verify constraints.

## 10. Verification Checklist
Concrete final checks.
```

## 8. Risk Controls

### Risk: Losing useful old research

Control:

- archive, do not delete,
- summarize extracted value,
- link archives from `DOCUMENTATION_INDEX.md`.

### Risk: Overwriting current code assumptions too early

Control:

- separate documentation cleanup from implementation refactor,
- mark code/config as legacy implementation until changed.

### Risk: Making root docs too large

Control:

- root docs route,
- blueprints explain,
- archives preserve.

### Risk: Gemma E4B underperforms on complex prompt writing

Control:

- templates,
- schemas,
- validators,
- skills,
- readiness gates,
- later LoRA/QLoRA/DPO only after data collection.

## 9. Recommended Next Action

Do not immediately rewrite all files.

Next best action:

1. Inventory all Amadeus text documents.
2. Produce a classification matrix.
3. Review the matrix.
4. Create `DOCUMENTATION_INDEX.md`.
5. Create the project-level `CLAUDE.md` and `AGENTS.md`.
6. Rewrite `README.md` and `REQUIREMENTS.md`.
7. Archive legacy local-AI research.
8. Create `IMPLEMENTATION_ROADMAP.md`.
9. Run final contradiction scan.

## 10. Definition Of Done

The cleanup is done when:

- A future agent can open `CLAUDE.md` and understand the project instantly.
- Codex can open `AGENTS.md` and know exactly how to work.
- The two new blueprints are clearly canonical.
- Old Qwen/cloud/provider documents are preserved but no longer misleading.
- The Amadeus root folder is readable, navigable, and implementation-ready.
- The documentation explicitly separates current target architecture from legacy code state.
