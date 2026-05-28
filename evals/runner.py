import importlib
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import amadeus.evals.cases
from amadeus.core.validator import RequirementsValidator
from amadeus.core.workflow import prepare_handoff_workspace
from amadeus.evals.schema import EvalCase, EvalRunReport
from amadeus.evals.scorer import score_case
from amadeus.models.requirements import RequirementsModel

logger = logging.getLogger(__name__)


def _generate_deterministic_requirements(case: EvalCase) -> RequirementsModel:
    reqs = RequirementsModel(
        project_name=case.input.project_name,
        display_name=case.title,
        short_description=case.description,
        project_type="evaluation-case",
        tech_stack=[],
        dependencies=[],
        specifications=[case.input.raw_text],
        quality_criteria=[],
        files_to_create=[],
    )
    # the validator usually populates any missing fields and logs
    return RequirementsValidator().validate(case.input.raw_text, reqs)


def run_eval_suite(
    mode: Literal["deterministic", "local_model"] = "deterministic",
    case_ids: list[str] | None = None,
) -> EvalRunReport:

    # 1. Discover all case_*.py files
    cases_dir = Path(amadeus.evals.cases.__file__).parent
    case_files = [f for f in cases_dir.glob("case_*.py") if not f.name.startswith("__")]

    all_cases: list[EvalCase] = []
    for cf in case_files:
        module_name = f"amadeus.evals.cases.{cf.stem}"
        mod = importlib.import_module(module_name)
        if hasattr(mod, "CASE"):
            all_cases.append(mod.CASE)

    if case_ids:
        all_cases = [c for c in all_cases if c.case_id in case_ids]

    scorecards = []
    for case in all_cases:
        logger.info(f"Running eval case: {case.case_id}")
        # a. Create tmp_path
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"amadeus_eval_{case.case_id}_"))

        # b. Copy fixture files
        source_paths = []
        for sf in case.input.source_files:
            sf_path = cases_dir / sf
            if sf_path.exists():
                dst = tmp_dir / sf_path.name
                shutil.copy(sf_path, dst)
                source_paths.append(dst)
            else:
                logger.warning(f"Fixture {sf} not found for case {case.case_id}")

        # c. Build RequirementsModel
        if mode == "deterministic":
            reqs = _generate_deterministic_requirements(case)
        else:
            # Here we would call the real analyzer. For now fallback to deterministic
            reqs = _generate_deterministic_requirements(case)

        # d. Call prepare_handoff_workspace
        result = prepare_handoff_workspace(
            requirements=reqs,
            raw_text=case.input.raw_text,
            output_dir=str(tmp_dir),
            approve_readiness=case.input.approve_readiness,
            approval_note=case.input.approval_note,
            source_files=source_paths,
        )

        # e. Score
        scorecard = score_case(case, result, tmp_dir)
        scorecards.append(scorecard)

        # We don't delete tmp_dir here to allow inspection on failure if needed
        # but normally we might want to clean up. For now we leave it.

    cases_run = len(scorecards)
    cases_passed = sum(1 for s in scorecards if s.passed)
    cases_failed = cases_run - cases_passed
    average_score = sum(s.overall for s in scorecards) / cases_run if cases_run > 0 else 0.0

    report = EvalRunReport(
        mode=mode,
        timestamp=datetime.now(timezone.utc).isoformat(),
        commit_hash="current",
        cases_run=cases_run,
        cases_passed=cases_passed,
        cases_failed=cases_failed,
        average_score=average_score,
        scorecards=scorecards,
    )

    # Save the report
    reports_dir = Path("_eval_runs")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_eval_report.json"
    report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    # Print summary table
    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Mode: {report.mode}")
    print(f"Cases Run: {report.cases_run}")
    print(f"Passed:    {report.cases_passed}")
    print(f"Failed:    {report.cases_failed}")
    print(f"Average Score: {report.average_score:.2f}")
    print("\nCase Breakdown:")
    for s in report.scorecards:
        status = "PASS" if s.passed else "FAIL"
        print(f"[{status}] {s.case_id} - Score: {s.overall:.2f}")
        if not s.passed:
            for err in s.errors:
                print(f"  - {err}")
    print("=" * 50 + "\n")

    return report
