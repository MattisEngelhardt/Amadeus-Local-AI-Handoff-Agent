from pathlib import Path

from amadeus.core.gap_analysis import GapAnalysisResult
from amadeus.core.workflow import HandoffBuildResult
from amadeus.evals.runner import run_eval_suite
from amadeus.evals.schema import EvalCase, EvalCaseExpectation, EvalCaseInput
from amadeus.evals.scorer import score_case
from amadeus.models.state import GapItem, ProjectState, ReadinessSnapshot


def _make_state(name: str) -> ProjectState:
    return ProjectState(project_name=name, display_name=name, main_goal="test")


def _make_gap_result() -> GapAnalysisResult:
    return GapAnalysisResult(blockers=[], assumptions=[], optional_items=[])


def test_eval_schema_round_trip():
    case = EvalCase(
        case_id="test_01",
        title="Test",
        description="A test",
        category="text_only",
        input=EvalCaseInput(raw_text="Test input"),
        expectation=EvalCaseExpectation(should_build=True),
    )
    js = case.model_dump_json()
    case_parsed = EvalCase.model_validate_json(js)
    assert case == case_parsed


def test_scorer_perfect_build(tmp_path):
    case = EvalCase(
        case_id="t1",
        title="T1",
        description="desc",
        category="text_only",
        input=EvalCaseInput(raw_text="Hello"),
        expectation=EvalCaseExpectation(should_build=True, min_readiness_score=100),
    )
    state = _make_state("t1")
    state.readiness = ReadinessSnapshot(score=100)
    result = HandoffBuildResult(
        project_path=str(tmp_path),
        state=state,
        gap_analysis=_make_gap_result(),
        readiness_report="",
        built=True,
        blocked=False,
        state_path=str(tmp_path),
    )
    (tmp_path / "MASTER_PROMPT.md").write_text(
        "# Master Prompt\n"
        + "\n".join(
            [
                "## Role",
                "## Core Directives",
                "## Project Identity",
                "## Requirements",
                "## Provided Context",
                "## Allowed Tools",
                "## Allowed Assumptions",
                "## Open Questions",
                "## Output Artifacts",
                "## Quality Criteria",
            ]
        )
    )
    for f in case.expectation.expected_generated_files:
        (tmp_path / f).touch()

    scorecard = score_case(case, result, tmp_path)
    assert scorecard.passed is True
    assert scorecard.requirement_extraction == 1.0
    assert scorecard.blocker_detection == 1.0
    assert scorecard.workspace_structure == 1.0


def test_scorer_blocked_when_expected(tmp_path):
    case = EvalCase(
        case_id="t2",
        title="T2",
        description="desc",
        category="missing_context",
        input=EvalCaseInput(raw_text="Hello"),
        expectation=EvalCaseExpectation(
            should_build=False,
            should_block=True,
            expected_blocker_keywords=["missing"],
        ),
    )
    state = _make_state("t2")
    state.gaps.append(
        GapItem(
            gap_id="g1", category="blocker", title="Missing file", detail="something is missing"
        )
    )
    result = HandoffBuildResult(
        project_path="",
        state=state,
        gap_analysis=_make_gap_result(),
        readiness_report="",
        built=False,
        blocked=True,
    )
    scorecard = score_case(case, result, tmp_path)
    assert scorecard.passed is True
    assert scorecard.blocker_detection == 1.0


def test_scorer_detects_missing_blocker(tmp_path):
    case = EvalCase(
        case_id="t3",
        title="T3",
        description="desc",
        category="missing_context",
        input=EvalCaseInput(raw_text="Hello"),
        expectation=EvalCaseExpectation(
            should_build=False,
            should_block=True,
            expected_blocker_keywords=["pdf"],
        ),
    )
    state = _make_state("t3")
    state.gaps.append(
        GapItem(
            gap_id="g1", category="blocker", title="Missing file", detail="something is missing"
        )
    )
    result = HandoffBuildResult(
        project_path="",
        state=state,
        gap_analysis=_make_gap_result(),
        readiness_report="",
        built=False,
        blocked=True,
    )
    scorecard = score_case(case, result, tmp_path)
    assert scorecard.passed is False
    assert scorecard.blocker_detection == 0.0


def test_runner_discovers_cases():
    import amadeus.evals.cases

    cases_dir = Path(amadeus.evals.cases.__file__).parent
    files = list(cases_dir.glob("case_*.py"))
    assert len(files) == 14


def test_deterministic_eval_case_01():
    report = run_eval_suite(mode="deterministic", case_ids=["case_01"])
    assert report.cases_run == 1
    assert report.scorecards[0].passed is True


def test_deterministic_eval_case_03():
    report = run_eval_suite(mode="deterministic", case_ids=["case_03"])
    assert report.cases_run == 1
    assert report.scorecards[0].passed is True


def test_deterministic_eval_case_04():
    report = run_eval_suite(mode="deterministic", case_ids=["case_04"])
    assert report.cases_run == 1
    assert report.scorecards[0].passed is True


def test_deterministic_eval_case_05():
    report = run_eval_suite(mode="deterministic", case_ids=["case_05"])
    assert report.cases_run == 1
    assert report.scorecards[0].passed is True
