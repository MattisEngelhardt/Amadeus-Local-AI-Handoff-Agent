## Codex /goal Prompt — Phase 9: Validation Suite

```
You are working on the Amadeus repository — a local Gemma 4 E4B prep agent that builds AI handoff workspaces for Codex, Claude Code, and Antigravity.

Phases 0–8 are complete. Your task is to fully implement Phase 9: Validation Suite.

Read these files first, in this order:
1. AGENTS.md (repository rules — non-negotiable constraints)
2. IMPLEMENTATION_ROADMAP.md (Phase 9 acceptance criteria)
3. REQUIREMENTS.md (Section 16 — Validation Requirements lists everything validators must check)
4. AMADEUS_WORKFLOW_BLUEPRINT.md (validation role in the workflow)
5. PROJECT_STATUS.md (current state — tells you exactly what exists and what is pending)
6. core/workspace_validator.py (current validators — CLAUDE.md and AGENTS.md anatomy checks already exist here)
7. core/validator.py (RequirementsValidator — deterministic validator for requirements)
8. core/gap_analysis.py (GapAnalyzer and GapAnalysisResult — gap detection logic)
9. core/generator.py (ProjectGenerator — generates all workspace files including MASTER_PROMPT.md, SOURCE_MAP.md, CONTEXT_INDEX.md)
10. core/material_ingestion.py (ingest_material function — material conversion pipeline)
11. core/transcriber.py (AudioTranscriber — transcription interface)
12. core/workflow.py (prepare_handoff_workspace — the build pipeline where validators are called)
13. models/state.py (ProjectState, TranscriptRecord, MaterialRecord, GapItem schemas)
14. models/requirements.py (RequirementsModel schema)
15. tests/ (all existing test files — understand patterns, fixtures, and naming)

## What Phase 9 requires

Phase 9 creates a comprehensive validation suite that prevents weak, incomplete, or structurally broken workspaces from being handed off. The validators must be individually callable, testable, and integrated into the existing build pipeline in `core/workflow.py`.

Currently `core/workspace_validator.py` already has:
- `validate_workspace()` — checks canonical files, directories, English names, source map references, and CLAUDE.md/AGENTS.md anatomy
- `validate_claude_md_anatomy()` — checks 10 required sections
- `validate_agents_md_anatomy()` — checks 8 required sections

Phase 9 expands this into a complete validation suite by adding 5 NEW validators plus hardening the 2 existing anatomy validators.

### A. Create `core/validation_suite.py` (NEW FILE)

This is the central validation orchestrator. It collects results from all individual validators and produces a unified `ValidationReport`.

Define these models:

```python
class ValidationIssue(BaseModel):
    validator: str          # e.g. "transcript", "prompt", "source_map"
    severity: Literal["error", "warning", "info"]
    message: str
    file_path: str = ""     # which file has the issue, if applicable

class ValidationReport(BaseModel):
    issues: list[ValidationIssue]
    passed: bool            # True if zero errors
    error_count: int
    warning_count: int
    info_count: int
    validators_run: list[str]
    timestamp: str

    def summary(self) -> str:
        """Return a human-readable multi-line summary."""
```

Add a main orchestrator function:

```python
def run_validation_suite(
    project_path: Path,
    state: ProjectState | None = None,
    requirements: RequirementsModel | None = None,
    raw_text: str = "",
) -> ValidationReport:
```

This function calls ALL validators in sequence, collects their issues, and returns a single `ValidationReport`. Each validator returns `list[ValidationIssue]`.

### B. Add Transcript Validator

Add function `validate_transcript(project_path, state) -> list[ValidationIssue]`:

Checks:
1. If state has `transcripts`, verify `raw_transcript_path` files exist under `project_path / "_logs/"` or the project path
2. If a transcript's `cleaned_transcript_path` is set, verify the file exists
3. Check that `_logs/raw_input.md` exists and is not empty (this is always created by the generator)
4. If `_logs/raw_input.md` exists, check it contains more than just the header (i.e., actual content beyond `# Raw Input`)
5. Severity: missing raw_input.md = error; empty raw input = warning; missing cleaned transcript = warning

### C. Add Prompt Validator

Add function `validate_prompt(project_path) -> list[ValidationIssue]`:

Checks:
1. `MASTER_PROMPT.md` exists
2. `MASTER_PROMPT.md` is not empty
3. `MASTER_PROMPT.md` contains required section headers: "Context", "Role", "Goal", "Requirements", "Non-Goals", "Working Materials", "Output Expectations", "Working Method", "Quality Criteria", "Open Questions" (these are the sections the generator creates — check `core/generator.py` `_master_prompt` method)
4. `MASTER_PROMPT.md` does not contain template placeholder patterns like `{{ }}` or `{% %}` (would indicate a rendering failure)
5. Severity: missing file = error; missing section = warning; template remnants = error

### D. Add Gap Analysis Validator

Add function `validate_gap_analysis(project_path, state) -> list[ValidationIssue]`:

Checks:
1. `_logs/gap_analysis.json` exists (created by `state_store.save_gap_analysis`)
2. If it exists, it is valid JSON and parseable
3. If state is provided, check consistency: the number of gaps in the JSON matches `len(state.gaps)`
4. Check that no `blocker` gaps have `status == "open"` while the workspace phase is `handoff_ready` (would indicate the readiness gate was bypassed)
5. If state has `readiness.score < 50` and the workspace was built, emit a warning about low readiness
6. Severity: missing gap file = warning (it's in _logs); invalid JSON = error; open blocker in handoff_ready = error; low readiness = warning

### E. Add Material Coverage Validator

Add function `validate_material_coverage(project_path, state) -> list[ValidationIssue]`:

Checks:
1. Every `MaterialRecord` in state with `status == "converted"` has its `context_path` file actually existing under the project path
2. Every `MaterialRecord` in state with `status == "converted"` has its `original_path` file existing under the project path
3. Check `_context/` directory — if state has converted materials, context dir should not be empty (beyond just README.md)
4. Check `_sources/` directory — if state has materials, sources dir should not be empty (beyond just README.md)
5. Any material with `status == "failed"` emits a warning including the extraction_notes
6. Severity: missing converted file = error; missing original = warning; failed material = warning

### F. Add Source Map Validator

Add function `validate_source_map(project_path, state) -> list[ValidationIssue]`:

This ENHANCES the existing source map check in `workspace_validator.py` (which currently only checks backtick-referenced paths).

Checks:
1. `SOURCE_MAP.md` exists
2. `SOURCE_MAP.md` is not empty
3. If state has materials, every material's `original_path` appears somewhere in SOURCE_MAP.md
4. If state has materials, every material's `context_path` (when set) appears somewhere in SOURCE_MAP.md
5. All `_sources/X` paths referenced in SOURCE_MAP.md actually exist (already done in workspace_validator, but now with proper severity)
6. All `_context/X` paths referenced in SOURCE_MAP.md actually exist (already done in workspace_validator, but now with proper severity)
7. Check that `CONTEXT_INDEX.md` exists and is consistent — if state has N materials, CONTEXT_INDEX.md should reference them
8. Severity: missing SOURCE_MAP.md = error; material not in map = warning; broken reference = error; inconsistent count = warning

### G. Add Workspace Tree Validator

Add function `validate_workspace_tree(project_path) -> list[ValidationIssue]`:

Checks:
1. All 9 canonical files exist: CLAUDE.md, AGENTS.md, MASTER_PROMPT.md, PROJECT_BRIEF.md, REQUIREMENTS.md, DECISIONS.md, NEXT_STEPS.md, CONTEXT_INDEX.md, SOURCE_MAP.md
2. All 5 canonical directories exist: _context/, _sources/, _skills/, _versions/, _logs/
3. No canonical file is empty (zero bytes after stripping whitespace)
4. All root-level file and folder names are ASCII-safe (regex: `^[a-zA-Z0-9_.-]+$`)
5. Check that `_versions/` contains at least one snapshot (the build creates an initial one via `versioning.py`)
6. Severity: missing file = error; missing directory = error; empty file = warning; non-ASCII name = warning; no version snapshot = info

### H. Harden existing CLAUDE.md and AGENTS.md anatomy validators

The existing `validate_claude_md_anatomy` and `validate_agents_md_anatomy` in `core/workspace_validator.py` return lists of missing section names. Wrap them into the new validation suite format:

Add function `validate_handoff_anatomy(project_path) -> list[ValidationIssue]`:

1. Call `validate_claude_md_anatomy` — each missing section becomes an error-severity issue
2. Call `validate_agents_md_anatomy` — each missing section becomes an error-severity issue
3. Check that CLAUDE.md mentions `SOURCE_MAP.md` (it should, from the quicklinks section)
4. Check that CLAUDE.md mentions `CONTEXT_INDEX.md` (it should)
5. Check that AGENTS.md mentions `NEXT_STEPS.md` (it should, from implementation priorities)
6. Severity: missing anatomy section = error; missing cross-reference = warning

### I. Integrate into the build pipeline

Update `core/workflow.py` `prepare_handoff_workspace`:

1. After the existing `validate_workspace()` call (line ~143), also call `run_validation_suite()` passing the scaffolded path, state, requirements, and raw_text
2. Log the `ValidationReport.summary()` at INFO level
3. If the report has errors, log each error at WARNING level (do NOT abort the build — keep the current behavior of warn-only)
4. Save the validation report as `_logs/validation_report.md` inside the workspace:
   - Header with timestamp
   - Summary line: "X errors, Y warnings, Z info"
   - Validators run
   - All issues grouped by severity (errors first, then warnings, then info)
5. Also save as `_logs/validation_report.json` (the ValidationReport model dumped as JSON)

### J. Add comprehensive tests

In `tests/`, add or update:

#### 1. `test_validation_suite.py` (NEW FILE)

Test the individual validators AND the orchestrator:

**Transcript validator tests:**
- test_transcript_validator_passes_with_populated_raw_input
- test_transcript_validator_warns_on_empty_raw_input
- test_transcript_validator_errors_on_missing_raw_input

**Prompt validator tests:**
- test_prompt_validator_passes_complete_prompt
- test_prompt_validator_detects_missing_sections
- test_prompt_validator_detects_template_remnants

**Gap analysis validator tests:**
- test_gap_validator_passes_with_valid_gap_file
- test_gap_validator_warns_on_missing_gap_file
- test_gap_validator_errors_on_invalid_json
- test_gap_validator_errors_on_open_blocker_in_handoff_ready

**Material coverage validator tests:**
- test_material_validator_passes_with_converted_materials
- test_material_validator_errors_on_missing_context_file
- test_material_validator_warns_on_failed_material

**Source map validator tests:**
- test_source_map_validator_passes_complete_map
- test_source_map_validator_errors_on_broken_reference
- test_source_map_validator_warns_on_missing_material_in_map

**Workspace tree validator tests:**
- test_workspace_tree_passes_valid_workspace
- test_workspace_tree_errors_on_missing_canonical_file
- test_workspace_tree_errors_on_missing_canonical_directory
- test_workspace_tree_warns_on_empty_file

**Handoff anatomy validator tests:**
- test_handoff_anatomy_passes_complete_files
- test_handoff_anatomy_errors_on_missing_claude_section
- test_handoff_anatomy_errors_on_missing_agents_section

**Orchestrator tests:**
- test_validation_suite_runs_all_validators
- test_validation_suite_report_counts_are_correct
- test_validation_suite_passed_is_false_when_errors_exist

Each test should use `tmp_path` fixtures. Create minimal but realistic workspace structures. Reuse patterns from existing tests (`test_workspace_validator.py` and `test_generator_handoff_files.py`).

#### 2. Update `test_workspace_validator.py`

Add a test that verifies `validate_workspace` still works correctly alongside the new validation suite (no regressions).

### K. Update project documentation

1. `IMPLEMENTATION_ROADMAP.md` — update Phase 9 status:
   `Status: Implemented on 2026-05-27. Validation suite with 7 validators (transcript, prompt, gap analysis, material coverage, source map, workspace tree, handoff anatomy) integrated into the build pipeline.`

2. `PROJECT_STATUS.md` — update:
   - Status date to 2026-05-27
   - Project phase line to mention Phase 9 completion
   - Add all Phase 9 implementation details to the "Implementation State" completed list:
     - `core/validation_suite.py` with ValidationReport, ValidationIssue models, 7 validators, and orchestrator
     - Integration into workflow with `_logs/validation_report.md` and `_logs/validation_report.json` output
   - Update "Known Gaps" to remove the Phase 9 validation item
   - Update "Next Priorities" to remove Phase 9 items and shift focus to Phase 10 and remaining gaps
   - Update "Observed verification" with Phase 9 test count

3. `dev_journey/CHANGELOG.md` — add a new entry at the TOP:
   ```
   ## 2026-05-27 - Validation Suite (Phase 9)

   Changed:
   - Created `core/validation_suite.py` with 7 validators: transcript, prompt, gap analysis, material coverage, source map, workspace tree, and handoff anatomy.
   - Added `ValidationReport` and `ValidationIssue` models for unified validation output.
   - Integrated the validation suite into `workflow.py` after workspace scaffolding.
   - Validation results are saved as `_logs/validation_report.md` and `_logs/validation_report.json` in every workspace.
   - Added comprehensive test coverage for all validators and the orchestrator.

   Verified:
   - pytest tests -q
   - ruff check .
   ```

### L. Create dev_journey snapshot

Create `dev_journey/snapshots/2026-05-27_phase9-validation-suite/`:
- Copy the new `core/validation_suite.py`
- Copy the updated `core/workflow.py`
- Copy the updated `core/workspace_validator.py`
- Write a `SNAPSHOT.md` explaining Phase 9 completion
- Write a `FILE_MANIFEST.md` listing all files in the snapshot

### M. Commit, push, and create GitHub release

This is the final mandatory step. Do NOT skip any part of it.

1. Stage ALL changed and new files (validation suite, workflow, tests, docs, snapshot — everything)
2. Commit with message: `feat: Implement Phase 9 — validation suite with 7 validators and build pipeline integration`
3. Push ALL commits to origin/main: `git push origin main`
4. Create git tag `v4.0.0`: `git tag v4.0.0`
5. Push the tag: `git push origin v4.0.0`
6. Create a GitHub release WITH source zip attached:
   ```
   gh release create v4.0.0 --generate-notes --title "v4.0.0 — Phase 9: Validation Suite"
   ```
   This automatically attaches the source zip and tarball to the release.
7. Verify the release exists on GitHub: `gh release view v4.0.0`
8. Verify the zip download URL is present in the release output

The task is NOT complete until `git push origin main`, the tag push, AND the GitHub release with zip are all confirmed successful.

## Verification before commit

Run these commands and ensure they pass:
```
.\\.venv\\Scripts\\python.exe -m pytest tests -q
.\\.venv\\Scripts\\python.exe -m ruff check amadeus .github pyproject.toml
```

If the `.venv` interpreter is not available, use the available `python` interpreter:
```
python -m pytest tests -q
python -m ruff check .
```

If any test fails, fix it before committing. Do not skip tests or use --no-verify.

## Non-negotiable rules

- Do NOT add cloud LLM providers as required architecture
- Do NOT treat Amadeus as the final task executor — it prepares workspaces
- Keep all generated workspace file and folder names in English
- Do NOT modify config.yaml or requirements.txt unless the implementation change requires it
- Preserve existing test coverage — only add, don't remove tests
- Follow the existing code patterns (Pydantic models, Path handling, logging, `from __future__ import annotations`)
- The validation suite must use the same import style as existing code: `from amadeus.core.X import Y`
- Validators must be pure functions or simple classes — no cloud calls, no Ollama calls, no network
- Every validator must be individually importable and testable
- `run_validation_suite` must gracefully handle missing state or requirements (produce info-level issues, not crashes)
- ALL changes MUST be pushed to GitHub before finishing — nothing stays local-only
- The GitHub release v4.0.0 with zip MUST exist before the task is considered done
```

## Verification

After the Codex instance completes:
1. Check that `core/validation_suite.py` exists and contains all 7 validator functions plus the orchestrator
2. Check that `tests/test_validation_suite.py` exists with comprehensive tests
3. Run `python -m pytest tests -q` and verify all tests pass (expect ~50+ tests total)
4. Run a smoke build: `python -m amadeus build-text --output-dir C:\tmp\phase9-test --project-name phase9-handoff --text "Build a Python REST API that serves weather data from a local SQLite database with authentication and rate limiting"`
5. Verify the generated workspace contains `_logs/validation_report.md` and `_logs/validation_report.json`
6. Verify the validation report shows all 7 validators ran
7. Verify `git log -1` shows the Phase 9 commit
8. Verify `git tag -l v4.0.0` shows the tag
9. Verify `gh release view v4.0.0` shows the release with source zip attached
10. Verify the dev_journey snapshot exists
