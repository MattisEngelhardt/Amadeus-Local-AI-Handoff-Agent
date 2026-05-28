# Phase 10 + 11 + 12 Implementation Plan

Status: Approved implementation plan for the next Codex/Claude Code/Antigravity agent
Date: 2026-05-28
Scope: Phases 10, 11, and 12 only — nothing else

This plan is written against the actual codebase as of commit `45527bd`
(Phase 9 complete). Every file path, function signature, import, model field,
and test pattern references the real code.

---

## Pre-Read Order

Before implementing anything, read these files in order:

1. `AGENTS.md` — non-negotiable repo rules
2. `IMPLEMENTATION_ROADMAP.md` — from line 207 onward (Phase 10–12 specs)
3. `PROJECT_STATUS.md` — current implementation state
4. `AMADEUS_WORKFLOW_BLUEPRINT.md` — target workflow architecture
5. `GEMMA_TO_AMADEUS_BLUEPRINT.md` — agent behavior layers
6. `core/workflow.py` — the current build pipeline
7. `core/validation_suite.py` — validation patterns (Phase 9)
8. `core/gap_analysis.py` — gap detection logic
9. `core/material_ingestion.py` — material converter
10. `core/analyzer.py` — Ollama/Gemma analysis interface
11. `core/ollama_client.py` — local LLM client
12. `core/generator.py` — workspace file generator
13. `core/scaffolder.py` — workspace folder creator
14. `core/state_store.py` — project state persistence
15. `models/state.py` — all Pydantic state models
16. `models/requirements.py` — RequirementsModel schema
17. `__main__.py` — current CLI entrypoint
18. `tests/test_readiness_workflow.py` — integration test patterns
19. `tests/test_validation_suite.py` — validator test patterns

---

## Non-Negotiable Constraints (from AGENTS.md)

- Core model: `gemma4:e4b` via Ollama. No cloud LLM providers as required architecture.
- Transcription: local `faster-whisper`. No OpenAI Whisper API in core path.
- Amadeus does NOT execute the final user task. It prepares handoff workspaces.
- Generated workspace file/folder names in English.
- Preserve raw inputs separately from cleaned/compiled context.
- Block workspace build while true blockers remain.
- Do not change `config.yaml` or `requirements.txt` during documentation-only work.
- When changing implementation, update tests and status in the same change.

---

## Phase 10: Baseline Evaluation Harness

### Goal

Make Amadeus quality measurable before expanding the agent surface. Create a
versioned eval suite that covers the most important workspace-generation
scenarios, with heavy emphasis on material handling.

### Why This Comes First

Phase 9 gave us structural validators. But validators only check "are the
files present and well-formed?" They do not check "did Amadeus correctly
detect blockers, map sources, extract requirements, and score readiness?"
Without eval cases, Phases 11 and 12 could silently degrade quality.

### New Files

```
evals/
├── __init__.py
├── schema.py                    # Pydantic models for eval cases and results
├── runner.py                    # Deterministic eval runner
├── scorer.py                    # Quality scoring logic
├── cases/
│   ├── __init__.py
│   ├── case_01_simple_text.py
│   ├── case_02_german_voice_app.py
│   ├── case_03_missing_pdf.py
│   ├── case_04_text_material.py
│   ├── case_05_multiple_materials.py
│   ├── case_06_conflicting_statements.py
│   ├── case_07_old_prompt_correction.py
│   ├── case_08_user_allows_assumptions.py
│   ├── case_09_codex_only_handoff.py
│   ├── case_10_claude_codex_handoff.py
│   ├── case_11_academic_missing_citation.py
│   ├── case_12_telegram_multi_message.py
│   ├── case_13_markdown_material.py
│   └── case_14_unreferenced_material.py
tests/
│   └── test_eval_suite.py       # Tests for the eval framework itself
```

### Modified Files

```
__main__.py                      # Add `eval` subcommand
IMPLEMENTATION_ROADMAP.md        # Update Phase 10 status
PROJECT_STATUS.md                # Update implementation state
dev_journey/CHANGELOG.md         # Add Phase 10 entry
```

### Step 1: Eval Schema (`evals/schema.py`)

Define Pydantic models that describe what an eval case is and what a scored
result looks like. These models will also be reused in Phase 12 (tool
validation) and Phase 24 (full eval loop).

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

class EvalCaseInput(BaseModel):
    """What Amadeus receives."""
    raw_text: str
    source_files: list[str] = Field(default_factory=list)
    # Relative paths within the case directory for fixture files.
    # The runner copies them to tmp_path before calling the pipeline.
    approve_readiness: bool = False
    approval_note: str = ""
    project_name: str = "eval-project"

class EvalCaseExpectation(BaseModel):
    """What the eval case expects Amadeus to produce."""
    should_build: bool
    should_block: bool = False
    min_readiness_score: int = 0
    max_readiness_score: int = 100
    expected_blocker_keywords: list[str] = Field(default_factory=list)
    expected_assumption_keywords: list[str] = Field(default_factory=list)
    expected_material_count: int = 0
    expected_material_statuses: list[str] = Field(default_factory=list)
    # e.g. ["converted", "converted"] or ["converted", "failed"]
    expected_generated_files: list[str] = Field(
        default_factory=lambda: [
            "CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md",
            "PROJECT_BRIEF.md", "REQUIREMENTS.md", "DECISIONS.md",
            "NEXT_STEPS.md", "CONTEXT_INDEX.md", "SOURCE_MAP.md",
        ]
    )
    expected_validation_passed: bool = True
    source_map_must_contain: list[str] = Field(default_factory=list)
    # Strings that must appear in SOURCE_MAP.md

class EvalCase(BaseModel):
    """One complete evaluation scenario."""
    case_id: str
    title: str
    description: str
    category: Literal[
        "text_only", "material", "voice", "missing_context",
        "contradiction", "handoff_target", "academic"
    ]
    input: EvalCaseInput
    expectation: EvalCaseExpectation

class EvalScorecard(BaseModel):
    """Scores for one eval case run."""
    case_id: str
    passed: bool
    requirement_extraction: float = 0.0   # 0.0–1.0
    blocker_detection: float = 0.0
    assumption_discipline: float = 0.0
    readiness_score_accuracy: float = 0.0
    source_map_completeness: float = 0.0
    prompt_section_completeness: float = 0.0
    workspace_structure: float = 0.0
    validation_status: float = 0.0
    overall: float = 0.0
    errors: list[str] = Field(default_factory=list)

class EvalRunReport(BaseModel):
    """Summary of a full eval run."""
    mode: Literal["deterministic", "local_model"]
    timestamp: str
    commit_hash: str = ""
    cases_run: int
    cases_passed: int
    cases_failed: int
    average_score: float
    scorecards: list[EvalScorecard]
```

### Step 2: Eval Cases (14 Cases, Material-Heavy)

Each case is a Python file that exports a single `CASE: EvalCase` variable.
This keeps cases inspectable, diffable, and easy to extend.

The following cases are required. Implement them as described:

**Case 01: Simple text-only project** (`case_01_simple_text.py`)
- Input: "Build a Python REST API that serves weather data from a local SQLite database."
- No materials, no blockers expected.
- Expected: builds, readiness >= 70, no open blockers.

**Case 02: German voice-style app idea** (`case_02_german_voice_app.py`)
- Input: "Ich brauch eine App die meine Studiennotizen zusammenfasst und daraus Karteikarten macht. Am besten mit Python und einer einfachen Web-Oberfläche."
- No materials. German input, English workspace.
- Expected: builds, project_name is English, specifications extracted.

**Case 03: Missing PDF reference** (`case_03_missing_pdf.py`)
- Input: "Build a report from the attached PDF file and preserve citations."
- No source_files provided.
- Expected: blocked, blocker keyword "materials" or "missing".

**Case 04: Text material ingestion** (`case_04_text_material.py`)
- Input: "Build the system based on the attached design notes."
- source_files: ["fixtures/design_notes.txt"] (create a fixture file with 5 lines of requirements text).
- Expected: builds, 1 material with status "converted", SOURCE_MAP.md contains "design_notes.txt".

**Case 05: Multiple materials** (`case_05_multiple_materials.py`)
- Input: "Use the attached specification and the architecture notes to build the workspace."
- source_files: ["fixtures/spec.md", "fixtures/arch_notes.txt"].
- Expected: builds, 2 materials with status "converted", both appear in SOURCE_MAP.md.

**Case 06: Conflicting user statements** (`case_06_conflicting_statements.py`)
- Input: "Build a REST API. Actually no, build a CLI tool. The output should be a web app."
- Expected: builds (the analyzer picks the last intent or merges), but assumptions are recorded.

**Case 07: Old prompt with correction** (`case_07_old_prompt_correction.py`)
- Input: "I previously said build a Django app. Forget that. Build a FastAPI service instead."
- Expected: builds, specifications mention FastAPI, not Django.

**Case 08: User explicitly allows assumptions** (`case_08_user_allows_assumptions.py`)
- Input: "Build a report from the attached PDF. Proceed with assumptions."
- No source_files, approve_readiness=True, approval_note="PDF will follow later."
- Expected: builds despite missing material, readiness_approved=True.

**Case 09: Codex-only handoff** (`case_09_codex_only_handoff.py`)
- Input: "Build a Node.js CLI tool. This workspace is exclusively for Codex."
- Expected: builds, AGENTS.md exists and references NEXT_STEPS.md.

**Case 10: Claude Code + Codex handoff** (`case_10_claude_codex_handoff.py`)
- Input: "Build a Python data pipeline. Hand off to Claude Code and Codex."
- Expected: builds, both CLAUDE.md and AGENTS.md have full anatomy.

**Case 11: Academic project with missing citation style** (`case_11_academic_missing_citation.py`)
- Input: "Schreibe eine Hausarbeit über maschinelles Lernen. Nutze wissenschaftliche Quellen."
- No source_files. Mentions "Quellen" (sources) but provides none.
- Expected: blocked, blocker keyword "materials" or "Quelle".

**Case 12: Telegram-style multi-message transcript** (`case_12_telegram_multi_message.py`)
- Input: Multi-line string simulating several short Telegram messages concatenated:
  "Build a task manager.\nAdd SQLite storage.\nMake it a CLI.\nUse Click for the CLI."
- Expected: builds, specifications capture the compound requirements.

**Case 13: Markdown material** (`case_13_markdown_material.py`)
- Input: "Build the project described in the attached specification."
- source_files: ["fixtures/project_spec.md"] (fixture with structured markdown: headings, lists, code blocks).
- Expected: builds, 1 material "converted", context file exists under _context/.

**Case 14: Unreferenced material** (`case_14_unreferenced_material.py`)
- Input: "Build a simple Python calculator."
- source_files: ["fixtures/random_notes.txt"].
- Text does NOT reference any files/materials.
- Expected: builds (no blocker because text doesn't mention materials), but material is ingested, optional gap "Unreferenced materials attached" is recorded.

### Fixture Files

Create these minimal fixture files under `evals/cases/fixtures/`:

- `design_notes.txt`: 5 lines of mock design requirements
- `spec.md`: Structured markdown with 3 headings and bullet lists
- `arch_notes.txt`: 4 lines of architecture notes
- `project_spec.md`: Longer markdown with headings, lists, and a code block
- `random_notes.txt`: 3 lines of unrelated notes

### Step 3: Eval Runner (`evals/runner.py`)

```python
def run_eval_suite(
    mode: Literal["deterministic", "local_model"] = "deterministic",
    case_ids: list[str] | None = None,
) -> EvalRunReport:
```

For `deterministic` mode (the default and the mode required for CI):

1. Discover all `case_*.py` files under `evals/cases/`.
2. For each case:
   a. Create a `tmp_path` (use `tempfile.mkdtemp`).
   b. Copy fixture files from `evals/cases/fixtures/` to `tmp_path`.
   c. Build a `RequirementsModel` by calling `TranscriptAnalyzer.analyze()`.
      **In deterministic mode, mock the Ollama call.** Use the
      `RequirementsValidator().validate()` fallback path that generates
      deterministic requirements from raw text (this is the path that tests
      already use — see `test_readiness_workflow.py` lines 13-25 for the
      pattern).
   d. Call `prepare_handoff_workspace(...)` with the case inputs.
   e. Score the result against `EvalCaseExpectation` using `scorer.py`.
3. Aggregate all scorecards into an `EvalRunReport`.
4. Save the report as `_eval_runs/<timestamp>_eval_report.json`.
5. Print a summary table to stdout.

For `local_model` mode (optional, requires Ollama running):

- Same flow but uses the real `TranscriptAnalyzer.analyze()` against the
  local `amadeus` model.
- This mode is NOT required for CI.

### Step 4: Eval Scorer (`evals/scorer.py`)

```python
def score_case(
    case: EvalCase,
    result: HandoffBuildResult,
    project_path: Path,
) -> EvalScorecard:
```

Scoring rules (each dimension is 0.0 to 1.0):

- **requirement_extraction**: 1.0 if `result.built == case.expectation.should_build`. 0.0 otherwise.
- **blocker_detection**: 1.0 if all expected_blocker_keywords appear in any blocker title/detail. 0.0 if expected blockers are missing.
- **assumption_discipline**: 1.0 if all expected_assumption_keywords appear in assumptions. 0.5 if some match. 0.0 if none.
- **readiness_score_accuracy**: 1.0 if `result.state.readiness.score` is within `[min_readiness_score, max_readiness_score]`. 0.0 otherwise.
- **source_map_completeness**: 1.0 if all `source_map_must_contain` strings appear in `SOURCE_MAP.md`. Proportional for partial matches.
- **prompt_section_completeness**: Reuse `PROMPT_REQUIRED_SECTIONS` from `validation_suite.py`. Score = sections_found / 10.
- **workspace_structure**: 1.0 if all `expected_generated_files` exist. Proportional otherwise.
- **validation_status**: 1.0 if `expected_validation_passed` matches the actual validation report's `passed` field.
- **overall**: Weighted average. blocker_detection and requirement_extraction weight 2x.

### Step 5: CLI Integration

Add to `__main__.py`:

```python
eval_parser = subparsers.add_parser("eval")
eval_parser.add_argument(
    "--mode",
    choices=["deterministic", "local_model"],
    default="deterministic",
)
eval_parser.add_argument("--case", nargs="*", default=None)
eval_parser.set_defaults(func=run_eval_command)
```

Implement `run_eval_command` that calls `run_eval_suite()` and prints
the summary. Return 0 if all cases pass, 1 if any fail.

### Step 6: Tests for the Eval Framework (`tests/test_eval_suite.py`)

- `test_eval_schema_round_trip`: Create an EvalCase, serialize to JSON, deserialize, assert equality.
- `test_scorer_perfect_build`: Feed a mock HandoffBuildResult that matches all expectations. Assert overall == 1.0.
- `test_scorer_blocked_when_expected`: Feed a blocked result where the case expected blocking. Assert passed == True.
- `test_scorer_detects_missing_blocker`: Feed a non-blocked result where the case expected a blocker. Assert passed == False.
- `test_runner_discovers_cases`: Assert the runner finds all 14 case files.
- `test_deterministic_eval_case_01`: Run case 01 through the full deterministic pipeline. Assert it passes.
- `test_deterministic_eval_case_03`: Run case 03 (missing PDF). Assert it correctly scores the blocker detection.
- `test_deterministic_eval_case_04`: Run case 04 (text material). Assert material ingestion is scored correctly.
- `test_deterministic_eval_case_05`: Run case 05 (multiple materials). Assert both materials scored.

### Step 7: Record Baseline Score

After all eval tests pass, run `python -m amadeus eval --mode deterministic`.
Record the baseline score in `PROJECT_STATUS.md` under a new section
"Baseline Evaluation Score" before Phase 11 starts.

### Phase 10 Verification

```bash
python -m pytest tests -q
python -m ruff check .
python -m amadeus eval --mode deterministic
```

All 14 eval cases must produce scorecards. Overall pass rate and average
score are recorded. No case may crash the runner.

---

## Phase 11: Global Terminal Agent CLI

### Goal

Make Amadeus feel like a real terminal agent command, not a Python module
invocation. Add project lifecycle commands and an active project registry.

### New Files

```
core/
│   ├── cli.py                   # Click/argparse command surface
│   └── project_registry.py      # Active project tracking
```

### Modified Files

```
__main__.py                      # Wire new commands into the existing entrypoint
core/state_store.py              # Add load_from_registry, list_projects
models/state.py                  # Add ProjectRegistryEntry model
```

### Step 1: Project Registry Model (`models/state.py`)

Add to the existing `models/state.py`:

```python
class ProjectRegistryEntry(BaseModel):
    project_name: str
    display_name: str
    project_path: str
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    phase: ProjectPhase = ProjectPhase.CONTEXT_COLLECTION
    readiness_score: int = 0
    is_active: bool = False
```

### Step 2: Project Registry (`core/project_registry.py`)

```python
REGISTRY_DIR = Path.home() / ".amadeus"
REGISTRY_FILE = REGISTRY_DIR / "projects.json"

class ProjectRegistry:
    def register(self, entry: ProjectRegistryEntry) -> None: ...
    def set_active(self, project_name: str) -> None: ...
    def get_active(self) -> ProjectRegistryEntry | None: ...
    def list_projects(self) -> list[ProjectRegistryEntry]: ...
    def remove(self, project_name: str) -> None: ...
    def update_state(self, project_name: str, state: ProjectState) -> None: ...
    def _load(self) -> list[ProjectRegistryEntry]: ...
    def _save(self, entries: list[ProjectRegistryEntry]) -> None: ...
```

Storage: `~/.amadeus/projects.json` — a JSON array of `ProjectRegistryEntry`.
The registry is purely a lookup table. Actual project state lives in the
project's own `_logs/amadeus_state.json`.

### Step 3: CLI Commands (`__main__.py` expansion)

Expand the existing argparse structure. Do NOT switch to Click — keep the
existing `argparse` pattern. Add these subcommands:

**`amadeus new "Build a local REST API from my notes"`**
- Calls `TranscriptAnalyzer.analyze()` on the quoted text.
- Creates a new project directory (default: `~/.amadeus/projects/<project_name>/`
  or `--output-dir` if given).
- Registers the project in the registry as active.
- Runs gap analysis and prints the readiness summary.
- Does NOT build yet — leaves the project in `context_collection`.

**`amadeus add <file_path> [<file_path> ...]`**
- Resolves the active project from the registry.
- Calls `_ingest_materials()` from `workflow.py` for each file.
- Updates project state.
- Re-runs gap analysis and prints updated readiness.

**`amadeus status`**
- Loads active project state from `_logs/amadeus_state.json`.
- Prints: project name, phase, readiness score, material count, blocker count,
  assumption count.

**`amadeus gaps`**
- Loads active project state.
- Prints all gaps grouped by category: blockers first, then assumptions,
  then optional items.
- For each gap: title, detail, question (if any), status.

**`amadeus materials`**
- Loads active project state.
- Prints material table: source_id, original_path, context_path, status, notes.

**`amadeus build`**
- Loads active project state.
- Re-runs the full `prepare_handoff_workspace()` pipeline.
- Includes `--approve-readiness` and `--approval-note` flags.
- Updates registry with new phase and readiness.

**`amadeus validate`**
- Runs `run_validation_suite()` on the active project's workspace.
- Prints the validation report summary.

**`amadeus eval`** (already added in Phase 10)

**`amadeus projects`**
- Lists all registered projects with: name, path, phase, readiness, active marker.

**`amadeus use <project_name>`**
- Sets a different project as active.

**`amadeus open`**
- Prints the active project's path.
- On Windows: opens the folder in Explorer (`os.startfile`).

**`amadeus check-runtime`** (already exists — keep as-is)

**`amadeus build-text`** (already exists — keep as-is for backward compatibility)

### Step 4: Wire Into Existing Entrypoint

The existing `__main__.py` uses `argparse` with `subparsers`. Keep this
pattern. Add each new subcommand as a new parser with its own `set_defaults(func=...)`.

Refactor `build_text()` to share pipeline code with the new `build` command.
Extract a shared `_run_build_pipeline()` function that both call.

### Step 5: Backward Compatibility

`python -m amadeus build-text --text "..."` must keep working exactly as before.
The new `amadeus new` / `amadeus build` workflow is additive.

### Step 6: Global Command Installation

Add a `pyproject.toml` `[project.scripts]` entry:

```toml
[project.scripts]
amadeus = "amadeus.__main__:main"
```

If `pyproject.toml` does not exist yet, create it with minimal metadata.
If it exists, add the scripts section.

Add `amadeus install-commands` to print instructions for making the
`amadeus` command globally available:

```
pip install -e .
# or
pip install --user -e .
# Then verify:
amadeus check-runtime
```

### Step 7: Tests

**`tests/test_project_registry.py`** (new file):
- `test_register_and_list`: Register two projects, list returns both.
- `test_set_active`: Register two, set one active, verify `get_active()`.
- `test_remove`: Register, remove, list is empty.
- `test_update_state`: Register, update with new phase, verify.
- `test_registry_persists_to_disk`: Register, create new `ProjectRegistry` instance, verify data is there.

**`tests/test_cli_commands.py`** (new file):
- `test_new_command_creates_project`: Call `main(["new", "Build a test project", "--output-dir", str(tmp_path)])`. Assert project directory exists and registry has an entry.
- `test_add_command_ingests_material`: Create project, then `main(["add", str(fixture_file)])`. Assert material appears in state.
- `test_status_command_prints_summary`: Create project, capture stdout of `main(["status"])`. Assert it contains project name and readiness score.
- `test_build_command_creates_workspace`: Create project, `main(["build"])`. Assert workspace files exist.
- `test_projects_command_lists_all`: Create two projects, capture stdout of `main(["projects"])`. Assert both names appear.
- `test_use_command_switches_active`: Create two projects, `main(["use", "second-project"])`. Assert `get_active()` returns the second.
- `test_build_text_backward_compatibility`: Run the old `main(["build-text", "--text", "...", "--output-dir", str(tmp_path)])`. Assert it still works.

### Phase 11 Verification

```bash
python -m pytest tests -q
python -m ruff check .
python -m amadeus eval --mode deterministic
# Manual smoke on Windows PowerShell:
amadeus new "Build a local REST API for weather data"
amadeus add C:\tmp\test-notes.txt
amadeus status
amadeus gaps
amadeus build
amadeus validate
amadeus projects
```

---

## Phase 12: Agent Tool Runtime And Mode Orchestrator

### Goal

Transform Amadeus from a linear CLI pipeline into a controlled local agent
that can decide which tool to run next. Gemma proposes structured actions.
Python executes tools. Validators verify results. State records every action.

### Architecture Boundary (from IMPLEMENTATION_ROADMAP.md)

- Ollama is the local model runtime. It stores the Amadeus model identity,
  parameters, and structured-output settings.
- The Amadeus application is the agent control layer. It owns tools,
  state, validation, and the agent loop.
- The agent loop is: Observe -> Summarize -> Decide -> Act -> Validate -> Record.

### New Files

```
core/
│   ├── tool_registry.py         # Tool definitions and typed contracts
│   ├── tool_executor.py         # Safe tool execution with logging
│   ├── agent_loop.py            # The ReAct-style agent orchestrator
│   └── modes.py                 # Mode definitions and mode prompts
models/
│   └── tools.py                 # Pydantic models for tool actions
```

### Modified Files

```
core/workflow.py                 # Expose pipeline steps as individual tools
core/ollama_client.py            # Add structured-output helper for tool decisions
models/state.py                  # Add ActionRecord model for agent loop logging
__main__.py                      # Add `amadeus agent` command
```

### Step 1: Tool Action Models (`models/tools.py`)

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Any

ToolName = Literal[
    "create_project",
    "save_raw_input",
    "transcribe_audio",
    "clean_transcript",
    "ingest_material",
    "run_gap_analysis",
    "render_prompt",
    "render_readiness",
    "build_workspace",
    "run_validation_suite",
    "write_decision",
    "create_snapshot",
    "inspect_link",
]

class ToolAction(BaseModel):
    """A single tool action proposed by Gemma."""
    tool: ToolName
    reason: str  # Why the agent chose this action
    parameters: dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    """The outcome of executing a tool action."""
    tool: ToolName
    success: bool
    output: str = ""
    error: str = ""
    state_changed: bool = False

class AgentDecision(BaseModel):
    """Structured output schema for Gemma's next-action decision."""
    observation: str    # What the agent observes about current state
    reasoning: str      # Why it chose this action
    action: ToolAction
    done: bool = False  # True when the agent believes no more actions needed

class ActionRecord(BaseModel):
    """Persisted log of one agent loop iteration."""
    step: int
    decision: AgentDecision
    result: ToolResult
    timestamp: str = Field(default_factory=utc_now_iso)
```

### Step 2: Tool Registry (`core/tool_registry.py`)

Define each tool as a typed contract:

```python
@dataclass
class ToolContract:
    name: ToolName
    description: str
    required_params: list[str]
    optional_params: list[str]
    mode: str  # Which agent mode uses this tool

TOOL_REGISTRY: dict[ToolName, ToolContract] = {
    "create_project": ToolContract(
        name="create_project",
        description="Initialize a new Amadeus project with state and registry entry.",
        required_params=["raw_text"],
        optional_params=["project_name", "output_dir"],
        mode="intake",
    ),
    "save_raw_input": ToolContract(
        name="save_raw_input",
        description="Persist a raw text or voice input to the project state.",
        required_params=["raw_text", "channel", "kind"],
        optional_params=[],
        mode="intake",
    ),
    "ingest_material": ToolContract(
        name="ingest_material",
        description="Convert a source file into _sources/ and _context/.",
        required_params=["source_path"],
        optional_params=["source_id"],
        mode="intake",
    ),
    "run_gap_analysis": ToolContract(
        name="run_gap_analysis",
        description="Analyze gaps, blockers, and assumptions in the current state.",
        required_params=[],
        optional_params=[],
        mode="gap_analyst",
    ),
    "render_prompt": ToolContract(
        name="render_prompt",
        description="Generate or update MASTER_PROMPT.md from current state.",
        required_params=[],
        optional_params=[],
        mode="prompt_compiler",
    ),
    "render_readiness": ToolContract(
        name="render_readiness",
        description="Render the readiness gate report.",
        required_params=[],
        optional_params=[],
        mode="workspace_architect",
    ),
    "build_workspace": ToolContract(
        name="build_workspace",
        description="Generate and scaffold the full handoff workspace.",
        required_params=[],
        optional_params=["approve_readiness", "approval_note"],
        mode="build_orchestrator",
    ),
    "run_validation_suite": ToolContract(
        name="run_validation_suite",
        description="Run all 7 validators on the built workspace.",
        required_params=[],
        optional_params=[],
        mode="build_orchestrator",
    ),
    "write_decision": ToolContract(
        name="write_decision",
        description="Record a project decision in state.",
        required_params=["summary", "rationale"],
        optional_params=["approved_by_user"],
        mode="gap_analyst",
    ),
    "create_snapshot": ToolContract(
        name="create_snapshot",
        description="Create a version snapshot of the current workspace.",
        required_params=["reason"],
        optional_params=[],
        mode="build_orchestrator",
    ),
    # transcribe_audio, clean_transcript, inspect_link are registered
    # but their execute functions are stubs until Phase 14/15.
}
```

### Step 3: Tool Executor (`core/tool_executor.py`)

```python
class ToolExecutor:
    def __init__(self, state: ProjectState, project_path: Path):
        self.state = state
        self.project_path = project_path

    def execute(self, action: ToolAction) -> ToolResult:
        contract = TOOL_REGISTRY.get(action.tool)
        if not contract:
            return ToolResult(tool=action.tool, success=False,
                              error=f"Unknown tool: {action.tool}")
        # Validate required params
        for param in contract.required_params:
            if param not in action.parameters:
                return ToolResult(tool=action.tool, success=False,
                                  error=f"Missing required param: {param}")
        # Dispatch to the actual implementation
        handler = self._handlers.get(action.tool)
        if not handler:
            return ToolResult(tool=action.tool, success=False,
                              error=f"No handler for tool: {action.tool}")
        try:
            return handler(action.parameters)
        except Exception as exc:
            return ToolResult(tool=action.tool, success=False,
                              error=str(exc))
```

Each handler wraps an existing function from `workflow.py`, `gap_analysis.py`,
`material_ingestion.py`, etc. The executor NEVER calls Ollama directly —
only the agent loop does that.

Guardrails (implement as checks in `execute()`):
- No file writes outside the project workspace root.
- No build while open blockers exist (unless `approve_readiness` is True).
- No cloud LLM calls.
- No silent source invention.
- Every tool action logs intent and result to `state.action_log`.

### Step 4: Agent Modes (`core/modes.py`)

```python
class AgentMode(BaseModel):
    name: Literal[
        "intake", "transcription_review", "prompt_compiler",
        "gap_analyst", "workspace_architect", "build_orchestrator"
    ]
    system_prompt: str
    allowed_tools: list[ToolName]
    goal: str
    transition_condition: str  # Human-readable description

MODES: dict[str, AgentMode] = {
    "intake": AgentMode(
        name="intake",
        system_prompt="You are Amadeus in Intake Mode. ...",
        allowed_tools=["create_project", "save_raw_input",
                        "ingest_material", "inspect_link"],
        goal="Accept and register all raw inputs and materials.",
        transition_condition="All inputs received and registered.",
    ),
    "gap_analyst": AgentMode(
        name="gap_analyst",
        system_prompt="You are Amadeus in Gap Analyst Mode. ...",
        allowed_tools=["run_gap_analysis", "write_decision"],
        goal="Identify blockers, assumptions, and missing materials.",
        transition_condition="Gap analysis complete, all blocker questions formulated.",
    ),
    "prompt_compiler": AgentMode(
        name="prompt_compiler",
        system_prompt="You are Amadeus in Prompt Compiler Mode. ...",
        allowed_tools=["render_prompt"],
        goal="Generate a professional MASTER_PROMPT.md from state.",
        transition_condition="Prompt rendered and versioned.",
    ),
    "workspace_architect": AgentMode(
        name="workspace_architect",
        system_prompt="You are Amadeus in Workspace Architect Mode. ...",
        allowed_tools=["render_readiness"],
        goal="Plan workspace structure and check readiness.",
        transition_condition="Readiness gate passed or explicitly approved.",
    ),
    "build_orchestrator": AgentMode(
        name="build_orchestrator",
        system_prompt="You are Amadeus in Build Orchestrator Mode. ...",
        allowed_tools=["build_workspace", "run_validation_suite",
                        "create_snapshot"],
        goal="Build, validate, and snapshot the handoff workspace.",
        transition_condition="Workspace built, validated, and snapshotted.",
    ),
}
```

Write detailed system prompts for each mode. The prompts must include:
- The Agent Constitution (10 rules from GEMMA_TO_AMADEUS_BLUEPRINT.md §6).
- The allowed tools for this mode.
- The expected JSON output format (AgentDecision schema).
- The transition condition.

### Step 5: Agent Loop (`core/agent_loop.py`)

```python
class AgentLoop:
    MAX_STEPS = 20

    def __init__(
        self,
        state: ProjectState,
        project_path: Path,
        client: OllamaClient,
        model: str = "amadeus",
        dry_run: bool = False,
    ):
        self.state = state
        self.project_path = project_path
        self.executor = ToolExecutor(state, project_path)
        self.client = client
        self.model = model
        self.dry_run = dry_run
        self.action_log: list[ActionRecord] = []
        self.current_mode: str = "intake"

    def run(self, initial_text: str = "") -> ProjectState:
        for step in range(self.MAX_STEPS):
            mode = MODES[self.current_mode]

            # 1. Build context for Gemma
            context = self._build_context(mode, initial_text)

            # 2. Ask Gemma for next action
            decision = self._ask_gemma(context, mode)

            # 3. Validate action is allowed in current mode
            if decision.action.tool not in mode.allowed_tools:
                # Log violation, skip, continue
                ...

            # 4. Execute (or dry-run)
            if self.dry_run:
                result = ToolResult(tool=decision.action.tool, success=True,
                                    output="[dry-run] Not executed.")
            else:
                result = self.executor.execute(decision.action)

            # 5. Record
            record = ActionRecord(step=step, decision=decision, result=result)
            self.action_log.append(record)

            # 6. Check for mode transition or completion
            if decision.done:
                next_mode = self._next_mode()
                if next_mode is None:
                    break
                self.current_mode = next_mode

        return self.state

    def _ask_gemma(self, context: str, mode: AgentMode) -> AgentDecision:
        response = self.client.generate(
            prompt=context,
            model=self.model,
            system=mode.system_prompt,
            response_format="json",
            options={"temperature": 0.2},
        )
        return AgentDecision.model_validate_json(response)

    def _build_context(self, mode: AgentMode, initial_text: str) -> str:
        # Include: current state summary, previous actions, available tools,
        # current gaps/blockers, materials summary
        ...

    def _next_mode(self) -> str | None:
        order = ["intake", "gap_analyst", "prompt_compiler",
                 "workspace_architect", "build_orchestrator"]
        idx = order.index(self.current_mode)
        if idx + 1 < len(order):
            return order[idx + 1]
        return None
```

### Step 6: Ollama Client Enhancement (`core/ollama_client.py`)

Add a convenience method for structured JSON output:

```python
def generate_structured(
    self,
    prompt: str,
    model: str,
    system: str,
    response_model: type[BaseModel],
    options: dict[str, Any] | None = None,
) -> BaseModel:
    raw = self.generate(
        prompt=prompt, model=model, system=system,
        response_format="json", options=options,
    )
    return response_model.model_validate_json(raw)
```

### Step 7: State Model Extension (`models/state.py`)

Add `ActionRecord` import and a new field to `ProjectState`:

```python
action_log: list[ActionRecord] = Field(default_factory=list)
```

This enables full audit trail of every agent loop iteration.

### Step 8: CLI Integration

Add `amadeus agent` command:

```python
agent_parser = subparsers.add_parser("agent")
agent_parser.add_argument("text", nargs="?", default="")
agent_parser.add_argument("--dry-run", action="store_true")
agent_parser.add_argument("--max-steps", type=int, default=20)
agent_parser.add_argument("--model", default="amadeus")
agent_parser.add_argument("--output-dir", default="")
agent_parser.set_defaults(func=run_agent_command)
```

`run_agent_command`:
1. Create or load project from registry.
2. Instantiate `AgentLoop`.
3. Call `loop.run(initial_text=args.text)`.
4. Print summary of actions taken.
5. Save final state.

### Step 9: Preserve Deterministic Pipeline

The old `prepare_handoff_workspace()` in `workflow.py` must remain fully
functional. The agent loop is an ALTERNATIVE entry point, not a
replacement. Tests that use `prepare_handoff_workspace()` must keep passing.

The relationship is:
- `prepare_handoff_workspace()` = deterministic pipeline (for tests, CI, evals)
- `AgentLoop.run()` = autonomous agent pipeline (for interactive use)

Both share the same underlying tools and state models.

### Step 10: Tests

**`tests/test_tool_registry.py`** (new file):
- `test_all_tools_have_contracts`: Assert every ToolName has a TOOL_REGISTRY entry.
- `test_tool_contracts_have_valid_modes`: Assert every tool's mode is in MODES.

**`tests/test_tool_executor.py`** (new file):
- `test_execute_create_project`: Mock state, call create_project, assert state updated.
- `test_execute_ingest_material`: Provide a fixture .txt file, assert material ingested.
- `test_execute_run_gap_analysis`: Assert gap analysis produces result.
- `test_execute_build_workspace`: Assert full build produces workspace files.
- `test_execute_unknown_tool_fails`: Assert ToolResult.success is False.
- `test_execute_missing_required_param_fails`: Assert ToolResult.success is False.
- `test_guardrail_no_writes_outside_workspace`: Pass a path outside workspace root. Assert blocked.

**`tests/test_agent_loop.py`** (new file):
- `test_agent_loop_dry_run`: Run the loop in dry-run mode. Assert no files created, action_log populated.
- `test_agent_loop_mock_gemma_full_pipeline`: Mock `OllamaClient.generate()` to return valid `AgentDecision` JSON for each mode transition (intake -> gap_analyst -> prompt_compiler -> workspace_architect -> build_orchestrator). Assert the loop completes and produces a workspace.
- `test_agent_loop_stops_at_max_steps`: Mock Gemma to never return `done=True`. Assert loop stops at MAX_STEPS.
- `test_agent_loop_rejects_tool_not_in_mode`: Mock Gemma to return a tool not allowed in the current mode. Assert it's skipped/logged.

**`tests/test_modes.py`** (new file):
- `test_all_modes_have_system_prompts`: Assert every MODES entry has a non-empty system_prompt.
- `test_all_modes_reference_valid_tools`: Assert every tool in allowed_tools exists in TOOL_REGISTRY.
- `test_mode_system_prompts_contain_constitution`: Assert each prompt contains key constitution phrases ("Never build before context is complete", etc.).

### Phase 12 Verification

```bash
python -m pytest tests -q
python -m ruff check .
python -m amadeus eval --mode deterministic
# Verify deterministic pipeline is unbroken:
python -m amadeus build-text --text "Build a REST API" --output-dir C:\tmp\phase12-regression
# Agent dry-run:
python -m amadeus agent "Build a CLI tool for task management" --dry-run
```

---

## Implementation Order

Execute these steps sequentially. Do not skip ahead.

### Block A: Phase 10

1. Create `evals/__init__.py`, `evals/schema.py` with all models.
2. Create `evals/cases/__init__.py` and `evals/cases/fixtures/` with fixture files.
3. Implement all 14 eval case files.
4. Create `evals/scorer.py`.
5. Create `evals/runner.py`.
6. Add `eval` subcommand to `__main__.py`.
7. Create `tests/test_eval_suite.py`.
8. Run `pytest tests -q` and `ruff check .`.
9. Run `python -m amadeus eval --mode deterministic`.
10. Record baseline score in `PROJECT_STATUS.md`.

### Block B: Phase 11

11. Add `ProjectRegistryEntry` to `models/state.py`.
12. Create `core/project_registry.py`.
13. Add all new subcommands to `__main__.py` (new, add, status, gaps, materials, build, validate, projects, use, open).
14. Extract shared `_run_build_pipeline()` from `build_text()`.
15. Create `tests/test_project_registry.py`.
16. Create `tests/test_cli_commands.py`.
17. Update `pyproject.toml` with `[project.scripts]` entry.
18. Run `pytest tests -q` and `ruff check .`.
19. Run `python -m amadeus eval --mode deterministic` (must still pass).
20. Manual Windows PowerShell smoke for global `amadeus` command.

### Block C: Phase 12

21. Create `models/tools.py` with all Pydantic models.
22. Create `core/tool_registry.py` with TOOL_REGISTRY.
23. Create `core/modes.py` with MODES and system prompts.
24. Create `core/tool_executor.py` with handlers for each tool.
25. Create `core/agent_loop.py`.
26. Add `generate_structured()` to `core/ollama_client.py`.
27. Add `action_log` field to `ProjectState` in `models/state.py`.
28. Add `amadeus agent` subcommand to `__main__.py`.
29. Create `tests/test_tool_registry.py`.
30. Create `tests/test_tool_executor.py`.
31. Create `tests/test_agent_loop.py`.
32. Create `tests/test_modes.py`.
33. Run `pytest tests -q` and `ruff check .`.
34. Run `python -m amadeus eval --mode deterministic` (must still pass).
35. Verify `amadeus build-text` still works (regression).
36. Run `amadeus agent "Build a CLI tool" --dry-run`.

### Block D: Documentation and Snapshot

37. Update `IMPLEMENTATION_ROADMAP.md` Phase 10/11/12 status markers.
38. Update `PROJECT_STATUS.md` with new implementation details.
39. Update `dev_journey/CHANGELOG.md` with Phase 10/11/12 entries.
40. Create `dev_journey/snapshots/2026-05-28_phase10-11-12/` with:
    - `SNAPSHOT.md`
    - `FILE_MANIFEST.md`
    - Copies of key new files.

---

## Definition of Done

### Tests

- [ ] `python -m pytest tests -q` — all tests green (expect ~90+ tests)
- [ ] `python -m ruff check .` — clean
- [ ] `python -m amadeus eval --mode deterministic` — all 14 cases produce scorecards, no crashes

### Functional

- [ ] Eval suite runs 14 cases with quality scores
- [ ] Baseline score recorded in PROJECT_STATUS.md
- [ ] `amadeus new/add/status/gaps/materials/build/validate/projects/use` all work
- [ ] Project registry persists at `~/.amadeus/projects.json`
- [ ] `amadeus build-text` backward compatibility preserved
- [ ] Tool registry has 13 tool contracts
- [ ] Agent loop runs in dry-run mode with mocked Gemma
- [ ] Agent loop action log is persisted in state
- [ ] Mode system prompts contain Agent Constitution

### Blueprint Compliance

- [ ] No cloud LLM providers in core path
- [ ] Amadeus does not execute final user tasks
- [ ] English workspace names enforced
- [ ] Raw inputs preserved separately
- [ ] Build blocked while open blockers remain
- [ ] Tool decisions parsed through Pydantic, not free-form text
- [ ] Old deterministic pipeline still usable by tests

---

## Consciously Excluded

| Topic | When Instead |
|---|---|
| Real PDF/DOCX extraction | Phase 15 |
| Image/screenshot ingestion | Phase 15 |
| Telegram bot | Phase 20 |
| Desktop speechbar | Phase 21 |
| Memory system | Phase 22 |
| Validation repair autopilot | Phase 23 |
| Skill files content | Phase 18 |
| Fine-tuning | Phase 28 |
