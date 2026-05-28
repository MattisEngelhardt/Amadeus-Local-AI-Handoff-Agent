
## Codex /goal Prompt

```
You are working on the Amadeus repository — a local Gemma 4 E4B prep agent that builds AI handoff workspaces for Codex, Claude Code, and Antigravity.

Phases 0–7 are complete. Your task is to fully implement Phase 8: CLAUDE.md and AGENTS.md Generation.

Read these files first, in this order:
1. CLAUDE.md (project brain — non-negotiable constraints live here)
2. IMPLEMENTATION_ROADMAP.md (Phase 8 acceptance criteria)
3. REQUIREMENTS.md (Sections 12 and 13 — the 10-pillar CLAUDE.md contract and the AGENTS.md contract)
4. AMADEUS_WORKFLOW_BLUEPRINT.md (Section 15 and 16 — file roles and CLAUDE.md anatomy)
5. PROJECT_STATUS.md (current implementation state)
6. docs/templates/TARGET_CLAUDE_TEMPLATE.md (current template — too shallow)
7. docs/templates/TARGET_AGENTS_TEMPLATE.md (current template — too shallow)
8. core/generator.py (current _render_target_template method — only passes 4 variables)
9. models/state.py (ProjectState schema — all data available for injection)
10. models/requirements.py (RequirementsModel schema)
11. core/workspace_validator.py (current validators)
12. tests/ (all test files — understand test patterns)

## What Phase 8 requires

The generated CLAUDE.md and AGENTS.md in every handoff workspace must be **excellent, context-rich, immediately usable** by the executing agent. They are currently generic stubs.

### A. Rewrite TARGET_CLAUDE_TEMPLATE.md

The template must produce a CLAUDE.md with all 10 mandatory pillars:

1. **Role Alignment** — executing agent role, project name, goal, who prepared the workspace (Amadeus)
2. **Non-Negotiable Constraints** — injected from requirements.quality_criteria + any decisions/assumptions from state
3. **Session Continuity** — workspace generation timestamp, readiness score, phase, prompt version, approval note if any
4. **Semantic File Map** — a table mapping every workspace file and directory to its purpose and when to read it (like the existing Amadeus CLAUDE.md Section 5 pattern, but for the generated workspace)
5. **Quicklinks** — direct anchored links to key sections in MASTER_PROMPT.md, REQUIREMENTS.md, DECISIONS.md, NEXT_STEPS.md, CONTEXT_INDEX.md, SOURCE_MAP.md
6. **Prompt Modularity** — reference _skills/ folder, explain how to load skills, list included skills if any
7. **Tool and Source-Reading Rules** — prefer _context/ over _sources/, do not invent facts, check SOURCE_MAP.md, search sections before reading whole files, preserve citations
8. **Quality Rubrics** — injected quality criteria + standard Amadeus handoff quality rules
9. **Micro-Workflows** — forced check sequences: before implementing (read requirements → check sources → verify constraints), before changing scope (update DECISIONS.md), before finishing (run verification checklist)
10. **Verification Checklist** — checkbox list: read canonical reading order, checked SOURCE_MAP.md, followed NEXT_STEPS.md, preserved constraints, ran verification, documented remaining blockers

All pillars must be populated from real project data (ProjectState, RequirementsModel), not generic placeholders. Use Jinja2 template syntax with the variables listed below.

### B. Rewrite TARGET_AGENTS_TEMPLATE.md

The template must produce an AGENTS.md with:

1. **Project Direction** — goal, who prepared it, what the executing agent does
2. **Non-Negotiables** — constraints from requirements
3. **Source of Truth** — canonical reading order for the workspace
4. **File Map** — concise directory/file listing with purpose
5. **Commands** — build/test/lint commands if known, otherwise explicit "follow NEXT_STEPS.md"
6. **Context-Reading Rules** — prefer _context/, verify in SOURCE_MAP.md, do not invent
7. **Editing Discipline** — scope changes to task, update DECISIONS.md for scope changes, preserve sources and logs
8. **Definition of Done** — all requirements satisfied, non-goals respected, verification passed, blockers documented
9. **Implementation Priorities** — injected from NEXT_STEPS.md content or state

AGENTS.md must complement CLAUDE.md, not duplicate it. It must be concise and Codex-optimized.

### C. Update core/generator.py

Update the `_render_target_template` method to pass rich context to the templates:

Variables to inject (build them from the `requirements` and `state` parameters already available in `generate_all_files`):

- PROJECT_NAME: requirements.display_name
- PROJECT_GOAL: requirements.short_description
- CONSTRAINTS: formatted from requirements.quality_criteria
- COMMANDS: from state.workspace_plan or sensible defaults
- GENERATED_AT: current timestamp
- READINESS_SCORE: state.readiness.score
- READINESS_CAN_BUILD: state.readiness.can_build
- PHASE: state.phase.value
- APPROVAL_NOTE: state.approval_note or ""
- FILE_MAP_TABLE: generate a Markdown table of all workspace files with purpose (use the generated_files list or a predefined mapping)
- QUICKLINKS: formatted list of links to workspace files
- SKILLS_LIST: state.workspace_plan.skills_to_include
- QUALITY_CRITERIA: requirements.quality_criteria
- OPEN_QUESTIONS: state.open_questions
- OPEN_BLOCKERS: [gap.title for gap in state.gaps if gap.category == "blocker"]
- ASSUMPTIONS: [gap for gap in state.gaps if gap.category == "assumption"]
- DECISIONS_SUMMARY: formatted from state.decisions
- MATERIALS_SUMMARY: formatted from state.materials
- NEXT_STEPS_CONTENT: a concise ordered list from state or requirements
- EXECUTING_AGENTS: state.workspace_plan.executing_agents
- TECH_STACK: requirements.tech_stack
- DEPENDENCIES: requirements.dependencies
- SPECIFICATIONS: requirements.specifications

Refactor `_render_target_template` to accept `state: ProjectState | None` as well, so it can inject state data. Update the two calls in `generate_all_files` to pass state.

### D. Add CLAUDE.md and AGENTS.md anatomy validators

In `core/workspace_validator.py`, add two new validation functions:

1. `validate_claude_md_anatomy(project_path)` — checks that CLAUDE.md contains the 10 required section headers (Role Alignment, Constraints, Session Continuity, Semantic File Map, Quicklinks, Prompt Modularity, Source-Reading Rules, Quality Rubrics, Micro-Workflows, Verification Checklist). Return a list of missing sections.

2. `validate_agents_md_anatomy(project_path)` — checks that AGENTS.md contains the required sections (Project Direction, Non-Negotiables, Source of Truth, File Map, Commands, Context-Reading Rules, Editing Discipline, Definition of Done).

Integrate both into the existing `validate_workspace` function so they run automatically during workspace builds.

### E. Add tests

In `tests/`, add or update:

1. `test_workspace_validator.py` — add tests for the new anatomy validators:
   - test that a minimal CLAUDE.md missing sections is detected
   - test that a complete CLAUDE.md passes
   - test that AGENTS.md missing sections is detected
   - test that AGENTS.md complete passes

2. `test_generator_handoff_files.py` (new file) — test that `ProjectGenerator.generate_all_files` produces CLAUDE.md and AGENTS.md with all required sections when given a populated ProjectState and RequirementsModel. Verify:
   - CLAUDE.md contains all 10 pillar headers
   - AGENTS.md contains all required section headers
   - Project name appears in both files
   - Constraints appear in both files
   - Quality criteria appear in CLAUDE.md
   - Readiness score appears in CLAUDE.md session continuity section
   - SOURCE_MAP.md and CONTEXT_INDEX.md are referenced in quicklinks

### F. Update project documentation

1. `IMPLEMENTATION_ROADMAP.md` — add a status line to Phase 8:
   `Status: Implemented on 2026-05-26. Templates rewritten with 10-pillar CLAUDE.md and full AGENTS.md anatomy. Validators added.`

2. `PROJECT_STATUS.md` — update:
   - Project phase line to mention Phase 8 completion
   - Add Phase 8 items to the "Completed" list
   - Update "Next Priorities" to remove Phase 8 items and shift focus to Phase 9

3. `dev_journey/CHANGELOG.md` — add a new entry at the top:
   ```
   ## 2026-05-26 - CLAUDE.md & AGENTS.md Generation (Phase 8)

   Changed:
   - Rewrote TARGET_CLAUDE_TEMPLATE.md with all 10 mandatory pillars
   - Rewrote TARGET_AGENTS_TEMPLATE.md with full Codex-compatible anatomy
   - Updated generator to inject rich project state data into templates
   - Added CLAUDE.md and AGENTS.md anatomy validators
   - Added tests for anatomy validation and generated handoff file quality

   Verified:
   - pytest amadeus/tests -q
   - ruff check amadeus .github pyproject.toml
   ```

### G. Create dev_journey snapshot

Create `dev_journey/snapshots/2026-05-26_phase8-claude-agents-generation/`:
- Copy the new `docs/templates/TARGET_CLAUDE_TEMPLATE.md`
- Copy the new `docs/templates/TARGET_AGENTS_TEMPLATE.md`
- Copy `core/generator.py`
- Copy `core/workspace_validator.py`
- Write a `SNAPSHOT.md` explaining Phase 8 completion
- Write a `FILE_MANIFEST.md` listing all files in the snapshot

### H. Commit, push, and tag

1. Stage all changed files (templates, generator, validator, tests, docs, snapshot)
2. Commit with message: `feat: Implement Phase 8 — rich CLAUDE.md and AGENTS.md generation with anatomy validators`
3. Push to origin/main
4. Create a git tag: `v0.8.0-phase8-claude-agents`
5. Push the tag
6. Create a GitHub release from the tag using `gh release create v0.8.0-phase8-claude-agents --generate-notes --title "Phase 8: CLAUDE.md & AGENTS.md Generation"` with the source zip attached automatically

## Verification before commit

Run these commands and ensure they pass:
```
.\.venv\Scripts\python.exe -m pytest amadeus/tests -q
.\.venv\Scripts\python.exe -m ruff check amadeus .github pyproject.toml
```

If any test fails, fix it before committing. Do not skip tests or use --no-verify.

## Non-negotiable rules

- Do NOT add cloud LLM providers as required architecture
- Do NOT treat Amadeus as the final task executor — it prepares workspaces
- Keep all generated workspace file and folder names in English
- Do NOT modify config.yaml or requirements.txt unless the implementation change requires it
- Preserve existing test coverage — only add, don't remove tests
- Follow the existing code patterns (Pydantic models, Path handling, logging)
- Use the existing Jinja2 Environment setup in generator.py
```

## Verification

After the Codex instance completes:
1. Check that `docs/templates/TARGET_CLAUDE_TEMPLATE.md` contains all 10 pillar sections
2. Check that `docs/templates/TARGET_AGENTS_TEMPLATE.md` contains all required sections
3. Run `python -m amadeus build-text --output-dir C:\tmp\phase8-test --project-name phase8-handoff --text "Build a CLI tool that processes CSV files and generates summary reports with charts"` and verify the generated CLAUDE.md and AGENTS.md are rich and complete
4. Verify all tests pass
5. Verify the GitHub release exists with the tag
6. Verify the dev_journey snapshot exists
