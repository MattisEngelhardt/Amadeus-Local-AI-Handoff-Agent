# Amadeus Documentation Index

Status: Canonical navigation document
Date: 2026-05-24

This index defines each important Amadeus file, its authority, and how future agents should use it.

## Classification Matrix

| Path | Role | Status | Canonical? | Use |
|---|---|---:|---:|---|
| `CLAUDE.md` | Project brain | Current | Yes | First file for Claude Code and similar agents working on this repo. |
| `AGENTS.md` | Codex instructions | Current | Yes | First file for Codex-compatible agents. |
| `README.md` | Human overview | Current | Yes | Quick project explanation and entrypoint. |
| `PROJECT_STATUS.md` | State tracker | Current | Yes | Shows implemented vs planned architecture. |
| `REQUIREMENTS.md` | Product requirements | Current | Yes | Canonical product requirements. |
| `AMADEUS_WORKFLOW_BLUEPRINT.md` | Workflow blueprint | Current | Yes | Detailed target workflow and handoff contract. |
| `GEMMA_TO_AMADEUS_BLUEPRINT.md` | Behavior blueprint | Current | Yes | Agent identity, modes, skills, schemas, validation, fine-tuning path. |
| `IMPLEMENTATION_ROADMAP.md` | Build plan | Current | Yes | Implementation phases and acceptance gates. |
| `DOCUMENTATION_INDEX.md` | Documentation map | Current | Yes | File authority and routing. |
| `docs/decisions/ARCHITECTURE_DECISIONS.md` | Decision log | Current | Yes | Canonical architecture decisions. |
| `docs/decisions/AMADEUS_DOCUMENTATION_CLEANUP_PLAN.md` | Historical cleanup plan | Historical | No | Explains why documentation was reorganized. |
| `docs/templates/TARGET_CLAUDE_TEMPLATE.md` | Target workspace template | Current | Yes | Blueprint for generated target `CLAUDE.md`. |
| `docs/templates/TARGET_AGENTS_TEMPLATE.md` | Target workspace template | Current | Yes | Blueprint for generated target `AGENTS.md`. |
| `dev_journey/README.md` | Project history guide | Current | Yes | Explains Amadeus snapshots and dev journey rules. |
| `dev_journey/CHANGELOG.md` | Project changelog | Current | Yes | Tracks meaningful project-level changes. |
| `dev_journey/RESTORE_GUIDE.md` | Restore guide | Current | Yes | Explains how to use snapshots safely. |
| `dev_journey/snapshots/` | Fallback snapshots | Historical | No | Curated restore points for major Amadeus states. |
| `docs/research/LOCAL_AI_RESEARCH_ARCHIVE.md` | Research archive | Archived | No | Useful patterns extracted from old local-AI notes. |
| `docs/research/LEGACY_QWEN_LLAMA_CPP_NOTES.md` | Legacy technical notes | Archived | No | Qwen/llama.cpp lessons only; not target architecture. |
| `docs/research/originals/LOCAL_AI_PLAN_ORIGINAL.md` | Preserved original | Archived | No | Full old research preserved for traceability. |
| `docs/research/originals/LOCAL_AI_AGENT_MASTERCLASS_ORIGINAL.md` | Preserved original | Archived | No | Full old Qwen/llama.cpp playbook preserved. |
| `docs/research/originals/LOCAL_LLM_AGENT_SETUP_ORIGINAL.md` | Preserved original | Archived | No | Full old root-level local/hybrid setup note preserved. |
| `config.yaml` | Runtime config | Implementation | No | Current prototype config; target update pending implementation refactor. |
| `requirements.txt` | Dependencies | Implementation | No | Current prototype dependencies; cleanup pending code refactor. |
| `main.py` | Prototype entrypoint | Implementation | No | Current desktop pipeline; still legacy-oriented. |
| `core/` | Prototype modules | Implementation | No | Current recorder/transcriber/analyzer/validator/generator/scaffolder code. |
| `models/` | Prototype schemas | Implementation | No | Current Pydantic models. |
| `ui/` | Prototype UI | Implementation | No | Desktop overlay/tray/notification components. |
| `templates/` | Runtime Jinja templates | Implementation | No | Current prototype templates; target replacement pending. |
| `tests/` | Prototype tests | Implementation | No | Current tests for legacy behavior. |
| `assets/` | Visual assets | Supporting | No | Current workflow image and other media. |

## One Source Of Truth

What is Amadeus?

- `README.md`
- `REQUIREMENTS.md`
- `AMADEUS_WORKFLOW_BLUEPRINT.md`

How does the workflow run?

- `AMADEUS_WORKFLOW_BLUEPRINT.md`

How does Gemma become Amadeus?

- `GEMMA_TO_AMADEUS_BLUEPRINT.md`

How should agents work in this repo?

- `CLAUDE.md`
- `AGENTS.md`

What is implemented vs planned?

- `PROJECT_STATUS.md`

How should the project be built?

- `IMPLEMENTATION_ROADMAP.md`

How is Amadeus' own dev journey tracked?

- `dev_journey/README.md`
- `dev_journey/CHANGELOG.md`
- `dev_journey/RESTORE_GUIDE.md`

Where is old local-AI research?

- `docs/research/`

## Provider And Model Reference Policy

Allowed as current architecture:

- Gemma 4 E4B.
- `gemma4:e4b`.
- Ollama.
- `faster-whisper`.

Allowed as executing environments:

- Codex.
- Claude Code.
- Antigravity.

Allowed only as legacy, rejected, or optional manual context:

- Qwen.
- llama.cpp.
- DeepSeek.
- Gemini.
- OpenAI API.
- Anthropic.
- Groq.
- NVIDIA NIM.
- OpenRouter.
- Cloud fallback.

## Archive Rules

Archived documents are preserved for research value only.

Do not use archived docs to override:

- the model decision,
- the runtime decision,
- the no-cloud-core constraint,
- the prep-agent role,
- the target handoff workspace contract.

If useful archived content should become current, extract the principle and add it to the owning canonical file instead of linking the legacy section as authority.
