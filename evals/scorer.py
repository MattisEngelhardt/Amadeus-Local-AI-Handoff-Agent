from pathlib import Path

from amadeus.core.validation_suite import PROMPT_REQUIRED_SECTIONS, run_validation_suite
from amadeus.core.workflow import HandoffBuildResult
from amadeus.evals.schema import EvalCase, EvalScorecard


def score_case(
    case: EvalCase,
    result: HandoffBuildResult,
    project_path: Path,
) -> EvalScorecard:
    errors: list[str] = []

    req_score = 1.0 if result.built == case.expectation.should_build else 0.0
    if result.built != case.expectation.should_build:
        errors.append(f"Expected build={case.expectation.should_build}, got build={result.built}")

    blocker_score = 1.0
    if case.expectation.expected_blocker_keywords:
        blockers = [g for g in result.state.gaps if g.category == "blocker"]
        blocker_text = " ".join([b.title + " " + b.detail for b in blockers]).lower()
        missing_blockers = [
            k for k in case.expectation.expected_blocker_keywords if k.lower() not in blocker_text
        ]
        if missing_blockers:
            blocker_score = 0.0
            errors.append(f"Missing expected blockers: {missing_blockers}")

    assumption_score = 1.0
    if case.expectation.expected_assumption_keywords:
        assumptions = [g for g in result.state.gaps if g.category == "assumption"]
        assumption_text = " ".join([a.title + " " + a.detail for a in assumptions]).lower()
        matched = sum(
            1 for k in case.expectation.expected_assumption_keywords if k.lower() in assumption_text
        )
        if matched == 0:
            assumption_score = 0.0
            errors.append("No expected assumptions found")
        elif matched < len(case.expectation.expected_assumption_keywords):
            assumption_score = 0.5
            errors.append("Some expected assumptions missing")

    score = result.state.readiness.score
    readiness_score = (
        1.0
        if case.expectation.min_readiness_score <= score <= case.expectation.max_readiness_score
        else 0.0
    )
    if readiness_score == 0.0:
        errors.append(
            f"Readiness score {score} outside [{case.expectation.min_readiness_score}, {case.expectation.max_readiness_score}]"
        )

    sm_score = 1.0
    if case.expectation.source_map_must_contain:
        # Score against the built workspace path, not the tmp_dir root
        ws_path = Path(result.project_path) if result.built else project_path
        sm_file = ws_path / "SOURCE_MAP.md"
        if sm_file.exists():
            sm_content = sm_file.read_text(encoding="utf-8")
            matched = sum(1 for s in case.expectation.source_map_must_contain if s in sm_content)
            sm_score = matched / len(case.expectation.source_map_must_contain)
            if sm_score < 1.0:
                errors.append("Missing source map entries")
        else:
            sm_score = 0.0
            errors.append("SOURCE_MAP.md not found")

    prompt_score = 1.0
    if case.expectation.should_build and result.built:
        ws_path = Path(result.project_path)
        prompt_file = ws_path / "MASTER_PROMPT.md"
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8")
            found = sum(1 for section in PROMPT_REQUIRED_SECTIONS if section in content)
            prompt_score = found / max(len(PROMPT_REQUIRED_SECTIONS), 1)
        else:
            prompt_score = 0.0
            errors.append("MASTER_PROMPT.md not found")

    ws_score = 1.0
    if case.expectation.should_build and result.built and case.expectation.expected_generated_files:
        ws_path = Path(result.project_path)
        found = sum(1 for f in case.expectation.expected_generated_files if (ws_path / f).exists())
        ws_score = found / len(case.expectation.expected_generated_files)
        if ws_score < 1.0:
            missing = [
                f for f in case.expectation.expected_generated_files if not (ws_path / f).exists()
            ]
            errors.append(f"Missing workspace files: {missing}")

    val_score = 1.0
    if result.built:
        ws_path = Path(result.project_path)
        try:
            val_report = run_validation_suite(ws_path)
            if val_report.passed != case.expectation.expected_validation_passed:
                val_score = 0.0
                errors.append(
                    f"Validation passed={val_report.passed}, expected={case.expectation.expected_validation_passed}"
                )
        except Exception as exc:
            val_score = 0.5
            errors.append(f"Validation error: {exc}")

    total_weight = 2.0 + 2.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0
    overall = (
        req_score * 2.0
        + blocker_score * 2.0
        + assumption_score * 1.0
        + readiness_score * 1.0
        + sm_score * 1.0
        + prompt_score * 1.0
        + ws_score * 1.0
        + val_score * 1.0
    ) / total_weight

    passed = overall >= 0.8 and req_score == 1.0 and blocker_score == 1.0
    if case.expectation.should_block and result.built:
        passed = False

    return EvalScorecard(
        case_id=case.case_id,
        passed=passed,
        requirement_extraction=req_score,
        blocker_detection=blocker_score,
        assumption_discipline=assumption_score,
        readiness_score_accuracy=readiness_score,
        source_map_completeness=sm_score,
        prompt_section_completeness=prompt_score,
        workspace_structure=ws_score,
        validation_status=val_score,
        overall=overall,
        errors=errors,
    )
