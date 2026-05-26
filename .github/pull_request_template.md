## Description
<!-- Describe your changes in detail. What problem does this PR solve? Why was this solution chosen? -->

## Type of Change
<!-- Please delete options that are not relevant -->
- [ ] 🐛 **Bugfix** (non-breaking change which fixes an issue)
- [ ] ✨ **New Feature** (non-breaking change which adds functionality)
- [ ] ⚙️ **Refactor / Optimization** (non-breaking change that improves code quality)
- [ ] 📝 **Documentation** (non-breaking change to docs/markdown files)
- [ ] 🛠️ **Infrastructure / CI** (changes to workflows, packages, or config)

## Verifikation & Tests
<!-- How did you test your changes? Paste command outputs, test runs, or manual screenshots here. -->
- [ ] **Automated Tests:** Run `pytest tests/` and verify that all tests pass.
- [ ] **Linter Check:** Run `ruff check .` to ensure no style violations.
- [ ] **Local Verification:** Run the Amadeus CLI smoke checks:
  ```powershell
  python -m amadeus check-runtime
  ```

## AI Handoff & Architecture Alignment
<!-- This project is managed with strict blueprints. Please verify alignment. -->
- [ ] **Blueprints:** Does this change align with `AMADEUS_WORKFLOW_BLUEPRINT.md` and `GEMMA_TO_AMADEUS_BLUEPRINT.md`?
- [ ] **Model constraints:** No cloud API dependencies added as required core architecture?
- [ ] **CLAUDE.md / AGENTS.md:** Are relevant commands and guidelines in `CLAUDE.md` and `AGENTS.md` still valid, or have they been updated in this PR?
- [ ] **Changelog:** Updated `dev_journey/CHANGELOG.md` if this is a meaningful milestone?
