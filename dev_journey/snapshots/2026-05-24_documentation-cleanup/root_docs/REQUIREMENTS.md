# Amadeus Product Requirements

Status: Canonical product requirements
Date: 2026-05-24
Authority: aligned with `AMADEUS_WORKFLOW_BLUEPRINT.md` and `GEMMA_TO_AMADEUS_BLUEPRINT.md`

## 1. Problem Statement

Starting a serious AI-assisted project currently requires too much manual preparation:

- recording or writing rough requirements,
- cleaning transcripts,
- collecting files and links,
- converting sources into usable Markdown,
- writing a strong master prompt,
- creating a target folder,
- assembling `CLAUDE.md`, `AGENTS.md`, source maps, and next steps,
- then finally starting the executing agent.

This preparation is repetitive, error-prone, and easy to under-specify. Missing files, unclear constraints, and vague prompts cause the executing agent to drift.

Amadeus exists to automate the preparation phase while keeping the user in control of important decisions.

## 2. Product Definition

Amadeus is a local Gemma 4 E4B prep agent that builds AI handoff workspaces.

It accepts raw voice, text, files, and links. It transcribes audio locally, preserves raw inputs, cleans and structures the context, detects missing information, asks targeted questions, and creates a complete handoff workspace for Codex, Claude Code, or Antigravity.

Amadeus does not execute the final project task.

## 3. Fixed Architecture Requirements

- Core LLM: `gemma4:e4b`.
- Runtime: Ollama.
- Speech-to-text: local `faster-whisper`.
- Primary input channels: Telegram and desktop speechbar.
- Workspace names and file names: English.
- Handoff through files, not live agent-to-agent messaging.
- No required cloud LLM provider in the core workflow.
- No Qwen, DeepSeek, Gemini, OpenAI API, Anthropic, Groq, NVIDIA NIM, or OpenRouter requirement in the target architecture.

Cloud tools may appear only as manual, optional, non-core review paths if explicitly requested later.

## 4. Users And Roles

User:

- provides goals, files, voice notes, text notes, links, examples, and answers to blockers.

Amadeus:

- receives and stores inputs,
- transcribes audio,
- cleans transcripts,
- builds prompt drafts,
- performs gap analysis,
- asks targeted questions,
- converts materials to Markdown,
- creates handoff files,
- validates workspace completeness.

Executing agent:

- Codex, Claude Code, or Antigravity reads the workspace and performs the final task.

## 5. Input Requirements

Amadeus must support:

- Telegram text messages,
- Telegram voice messages,
- Telegram files,
- desktop speechbar recordings,
- manually pasted text,
- PDFs,
- DOCX files,
- Markdown files,
- text files,
- links,
- old prompts,
- project examples,
- user preferences.

Every input must be traceable to its source.

## 6. Transcription Requirements

Audio transcription must be local by default:

- provider: `faster-whisper`,
- preferred model: `large-v3` when performance allows,
- fallback model: `distil-large-v3` or smaller local model when necessary,
- language: German for German user input.

For every voice input, Amadeus must preserve:

- raw transcript,
- cleaned transcript,
- uncertain terms,
- possible requirements,
- possible missing context.

Amadeus must not claim perfect transcription when uncertainty remains.

## 7. Context Collection Requirements

The context phase must collect enough information before build:

- project name,
- project goal,
- target execution environment,
- output expectations,
- constraints and non-goals,
- supplied materials,
- missing materials,
- known assumptions,
- open questions,
- preferred language and file conventions,
- quality criteria.

Amadeus must distinguish:

- user-provided facts,
- inferred assumptions,
- optional improvements,
- blockers.

## 8. Prompt Compiler Requirements

The master prompt must include:

- context,
- role,
- goal,
- requirements,
- non-goals,
- working materials,
- output expectations,
- working method,
- step-by-step plan,
- quality criteria,
- risks,
- open questions.

The prompt must be versioned and linked from the target workspace.

## 9. Gap Analysis Requirements

Amadeus must identify:

- ambiguous goals,
- missing files,
- missing source metadata,
- unclear target environment,
- missing format requirements,
- missing citation or style rules,
- contradictions between inputs,
- unsupported user expectations,
- hidden assumptions.

Gap categories:

- `Blocker`: must be answered or explicitly waived before build.
- `Assumption`: can proceed only when recorded.
- `Optional`: useful but not required.

## 10. Readiness Gate

Before building the workspace, Amadeus must show:

- project name,
- target path,
- main goal,
- planned executing agent,
- received materials,
- missing materials,
- open blockers,
- recorded assumptions,
- planned file tree,
- planned master files.

Build may proceed only when no blockers remain or the user explicitly allows documented assumptions.

## 11. Workspace Build Requirements

The target handoff workspace must use this contract:

```text
target_project/
|-- CLAUDE.md
|-- AGENTS.md
|-- MASTER_PROMPT.md
|-- PROJECT_BRIEF.md
|-- REQUIREMENTS.md
|-- DECISIONS.md
|-- NEXT_STEPS.md
|-- CONTEXT_INDEX.md
|-- SOURCE_MAP.md
|-- _context/
|-- _sources/
|-- _skills/
|-- _versions/
`-- _logs/
```

Original files must go to `_sources/`.
AI-optimized Markdown conversions must go to `_context/`.

## 12. Master `CLAUDE.md` Requirements

The generated `CLAUDE.md` is the heart and brain of the target workspace. It must function as a state machine for the executing agent.

Required pillars:

1. Role alignment.
2. Non-negotiable constraints.
3. Session continuity and current status.
4. Semantic file mapping.
5. Precise quicklinks and anchors.
6. Prompt modularity and skill delegation.
7. Tool and source-reading rules.
8. Quality rubrics.
9. Micro-workflows and forced checks.
10. Verification checklist and done criteria.

## 13. `AGENTS.md` Requirements

The generated `AGENTS.md` must be concise and Codex-compatible.

It must include:

- project rules,
- file map,
- commands,
- testing expectations,
- context-reading rules,
- editing discipline,
- definition of done,
- next implementation priorities.

It must complement `CLAUDE.md`, not replace it.

## 14. Source Mapping Requirements

Each material must be mapped:

```text
original source -> converted context file -> purpose -> referenced by
```

The system must never accept broken conversions silently.

## 15. Memory Requirements

Amadeus needs separated memory:

- user preference memory,
- project memory,
- skill memory,
- reflection memory.

Memory must not override user-provided facts or current project decisions.

## 16. Validation Requirements

Validators must check:

- transcript structure,
- prompt structure,
- gap analysis completeness,
- material coverage,
- source map correctness,
- `CLAUDE.md` anatomy,
- `AGENTS.md` usefulness,
- workspace tree completeness,
- handoff readiness.

Failed validation must trigger repair or targeted user questions.

## 17. Non-Goals

Amadeus does not:

- execute the final user project,
- generate production app code as the main deliverable,
- use cloud LLMs as required backend,
- hide missing context,
- overwrite original sources,
- treat archived Qwen/cloud research as current architecture,
- build before the readiness gate passes.

## 18. Acceptance Criteria

Amadeus is product-ready when:

- the user can start a project through Telegram voice or desktop speechbar,
- audio is transcribed locally,
- raw and cleaned transcripts are preserved,
- Amadeus creates a professional master prompt,
- missing context is identified and questioned,
- files are converted and source-mapped,
- the final workspace uses English agent conventions,
- `CLAUDE.md` and `AGENTS.md` are complete and immediately usable,
- `_sources/`, `_context/`, `_versions/`, and `_logs/` are populated correctly,
- the executing agent can start without manual context search.
