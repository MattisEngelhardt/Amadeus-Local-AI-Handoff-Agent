from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from amadeus.core.scaffolder import CANONICAL_DIRECTORIES
from amadeus.core.validator import CANONICAL_HANDOFF_FILES
from amadeus.core.workspace_validator import (
    validate_agents_md_anatomy,
    validate_claude_md_anatomy,
)
from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import ProjectPhase, ProjectState, utc_now_iso
from pydantic import BaseModel, Field

IssueSeverity = Literal["error", "warning", "info"]

VALIDATOR_NAMES = [
    "transcript",
    "prompt",
    "gap_analysis",
    "material_coverage",
    "source_map",
    "workspace_tree",
    "handoff_anatomy",
]

PROMPT_REQUIRED_SECTIONS = [
    "Context",
    "Role",
    "Goal",
    "Requirements",
    "Non-Goals",
    "Working Materials",
    "Output Expectations",
    "Working Method",
    "Quality Criteria",
    "Open Questions",
]


class ValidationIssue(BaseModel):
    validator: str
    severity: IssueSeverity
    message: str
    file_path: str = ""


class ValidationReport(BaseModel):
    issues: list[ValidationIssue] = Field(default_factory=list)
    passed: bool
    error_count: int
    warning_count: int
    info_count: int
    validators_run: list[str]
    timestamp: str

    def summary(self) -> str:
        """Return a human-readable multi-line summary."""

        status = "passed" if self.passed else "failed"
        lines = [
            f"Validation {status}: "
            f"{self.error_count} errors, {self.warning_count} warnings, "
            f"{self.info_count} info",
            "Validators run: " + ", ".join(self.validators_run),
        ]

        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                location = f" [{issue.file_path}]" if issue.file_path else ""
                lines.append(
                    f"- {issue.severity.upper()} {issue.validator}{location}: "
                    f"{issue.message}"
                )

        return "\n".join(lines)


def run_validation_suite(
    project_path: Path,
    state: ProjectState | None = None,
    requirements: RequirementsModel | None = None,
    raw_text: str = "",
) -> ValidationReport:
    """Run all workspace validators and return one unified report."""

    del raw_text

    project_path = Path(project_path)
    issues: list[ValidationIssue] = []
    validators_run: list[str] = []

    if requirements is None:
        issues.append(
            ValidationIssue(
                validator="validation_suite",
                severity="info",
                message=(
                    "Requirements model was not provided; requirement-specific "
                    "validation was skipped."
                ),
            )
        )

    validators: list[tuple[str, Callable[[], list[ValidationIssue]]]] = [
        ("transcript", lambda: validate_transcript(project_path, state)),
        ("prompt", lambda: validate_prompt(project_path)),
        ("gap_analysis", lambda: validate_gap_analysis(project_path, state)),
        ("material_coverage", lambda: validate_material_coverage(project_path, state)),
        ("source_map", lambda: validate_source_map(project_path, state)),
        ("workspace_tree", lambda: validate_workspace_tree(project_path)),
        ("handoff_anatomy", lambda: validate_handoff_anatomy(project_path)),
    ]

    for name, validator in validators:
        validators_run.append(name)
        try:
            issues.extend(validator())
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    validator=name,
                    severity="error",
                    message=f"Validator crashed: {exc}",
                )
            )

    error_count = _count_by_severity(issues, "error")
    warning_count = _count_by_severity(issues, "warning")
    info_count = _count_by_severity(issues, "info")
    return ValidationReport(
        issues=issues,
        passed=error_count == 0,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        validators_run=validators_run,
        timestamp=utc_now_iso(),
    )


def validate_transcript(
    project_path: Path | str,
    state: ProjectState | None,
) -> list[ValidationIssue]:
    project_path = Path(project_path)
    issues: list[ValidationIssue] = []

    if state is None:
        issues.append(
            ValidationIssue(
                validator="transcript",
                severity="info",
                message="Project state was not provided; transcript records were skipped.",
            )
        )
    else:
        for transcript in state.transcripts:
            raw_path = _resolve_workspace_path(project_path, transcript.raw_transcript_path)
            if not raw_path.exists() or not _is_under_project(project_path, raw_path):
                issues.append(
                    ValidationIssue(
                        validator="transcript",
                        severity="error",
                        message=(
                            "Transcript raw file is missing or outside the workspace: "
                            f"{transcript.raw_transcript_path}"
                        ),
                        file_path=transcript.raw_transcript_path,
                    )
                )

            if transcript.cleaned_transcript_path:
                cleaned_path = _resolve_workspace_path(
                    project_path,
                    transcript.cleaned_transcript_path,
                )
                if not cleaned_path.exists() or not _is_under_project(
                    project_path,
                    cleaned_path,
                ):
                    issues.append(
                        ValidationIssue(
                            validator="transcript",
                            severity="warning",
                            message=(
                                "Transcript cleaned file is missing or outside the "
                                f"workspace: {transcript.cleaned_transcript_path}"
                            ),
                            file_path=transcript.cleaned_transcript_path,
                        )
                    )

    raw_input_path = project_path / "_logs" / "raw_input.md"
    if not raw_input_path.exists():
        issues.append(
            ValidationIssue(
                validator="transcript",
                severity="error",
                message="_logs/raw_input.md is missing.",
                file_path="_logs/raw_input.md",
            )
        )
        return issues

    raw_input = raw_input_path.read_text(encoding="utf-8").strip()
    if not raw_input:
        issues.append(
            ValidationIssue(
                validator="transcript",
                severity="warning",
                message="_logs/raw_input.md is empty.",
                file_path="_logs/raw_input.md",
            )
        )
    elif _without_markdown_heading(raw_input, "Raw Input").strip() == "":
        issues.append(
            ValidationIssue(
                validator="transcript",
                severity="warning",
                message="_logs/raw_input.md contains no captured input beyond the header.",
                file_path="_logs/raw_input.md",
            )
        )

    return issues


def validate_prompt(project_path: Path | str) -> list[ValidationIssue]:
    project_path = Path(project_path)
    prompt_path = project_path / "MASTER_PROMPT.md"
    issues: list[ValidationIssue] = []

    if not prompt_path.exists():
        return [
            ValidationIssue(
                validator="prompt",
                severity="error",
                message="MASTER_PROMPT.md is missing.",
                file_path="MASTER_PROMPT.md",
            )
        ]

    content = prompt_path.read_text(encoding="utf-8")
    if not content.strip():
        issues.append(
            ValidationIssue(
                validator="prompt",
                severity="error",
                message="MASTER_PROMPT.md is empty.",
                file_path="MASTER_PROMPT.md",
            )
        )
        return issues

    for section in PROMPT_REQUIRED_SECTIONS:
        if not _has_markdown_section(content, section):
            issues.append(
                ValidationIssue(
                    validator="prompt",
                    severity="warning",
                    message=f"MASTER_PROMPT.md missing required section: {section}",
                    file_path="MASTER_PROMPT.md",
                )
            )

    if re.search(r"{{.*?}}|{%.*?%}", content, re.DOTALL):
        issues.append(
            ValidationIssue(
                validator="prompt",
                severity="error",
                message="MASTER_PROMPT.md contains unresolved template markers.",
                file_path="MASTER_PROMPT.md",
            )
        )

    return issues


def validate_gap_analysis(
    project_path: Path | str,
    state: ProjectState | None,
) -> list[ValidationIssue]:
    project_path = Path(project_path)
    gap_path = project_path / "_logs" / "gap_analysis.json"
    issues: list[ValidationIssue] = []
    payload: object | None = None

    if not gap_path.exists():
        issues.append(
            ValidationIssue(
                validator="gap_analysis",
                severity="warning",
                message="_logs/gap_analysis.json is missing.",
                file_path="_logs/gap_analysis.json",
            )
        )
    else:
        try:
            payload = json.loads(gap_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(
                ValidationIssue(
                    validator="gap_analysis",
                    severity="error",
                    message=f"_logs/gap_analysis.json is invalid JSON: {exc}",
                    file_path="_logs/gap_analysis.json",
                )
            )

    if state is None:
        issues.append(
            ValidationIssue(
                validator="gap_analysis",
                severity="info",
                message="Project state was not provided; gap-state checks were skipped.",
            )
        )
        return issues

    if isinstance(payload, dict):
        gap_count = _gap_count_from_payload(payload)
        if gap_count is not None and gap_count != len(state.gaps):
            issues.append(
                ValidationIssue(
                    validator="gap_analysis",
                    severity="warning",
                    message=(
                        "_logs/gap_analysis.json gap count does not match project "
                        f"state: {gap_count} != {len(state.gaps)}"
                    ),
                    file_path="_logs/gap_analysis.json",
                )
            )

    if state.phase == ProjectPhase.HANDOFF_READY:
        for gap in state.gaps:
            if gap.category == "blocker" and gap.status == "open":
                issues.append(
                    ValidationIssue(
                        validator="gap_analysis",
                        severity="error",
                        message=(
                            "Open blocker gap exists while workspace is handoff_ready: "
                            f"{gap.title}"
                        ),
                        file_path="_logs/gap_analysis.json",
                    )
                )

    if state.phase == ProjectPhase.HANDOFF_READY and state.readiness.score < 50:
        issues.append(
            ValidationIssue(
                validator="gap_analysis",
                severity="warning",
                message=(
                    "Workspace is handoff_ready with low readiness score: "
                    f"{state.readiness.score}/100"
                ),
                file_path="_logs/readiness_gate.md",
            )
        )

    return issues


def validate_material_coverage(
    project_path: Path | str,
    state: ProjectState | None,
) -> list[ValidationIssue]:
    project_path = Path(project_path)
    issues: list[ValidationIssue] = []

    if state is None:
        return [
            ValidationIssue(
                validator="material_coverage",
                severity="info",
                message="Project state was not provided; material records were skipped.",
            )
        ]

    converted_materials = [
        material for material in state.materials if material.status == "converted"
    ]

    for material in converted_materials:
        context_path = _resolve_workspace_path(project_path, material.context_path)
        if not material.context_path or not context_path.exists():
            issues.append(
                ValidationIssue(
                    validator="material_coverage",
                    severity="error",
                    message=(
                        "Converted material context file is missing: "
                        f"{material.context_path or '<empty>'}"
                    ),
                    file_path=material.context_path,
                )
            )

        original_path = _resolve_workspace_path(project_path, material.original_path)
        if not material.original_path or not original_path.exists():
            issues.append(
                ValidationIssue(
                    validator="material_coverage",
                    severity="warning",
                    message=(
                        "Converted material original file is missing: "
                        f"{material.original_path or '<empty>'}"
                    ),
                    file_path=material.original_path,
                )
            )

    if converted_materials and not _directory_has_content(project_path / "_context"):
        issues.append(
            ValidationIssue(
                validator="material_coverage",
                severity="error",
                message="_context/ has no converted material files.",
                file_path="_context",
            )
        )

    if state.materials and not _directory_has_content(project_path / "_sources"):
        issues.append(
            ValidationIssue(
                validator="material_coverage",
                severity="warning",
                message="_sources/ has no source material files.",
                file_path="_sources",
            )
        )

    for material in state.materials:
        if material.status == "failed":
            notes = "; ".join(material.extraction_notes) or "No extraction notes recorded."
            issues.append(
                ValidationIssue(
                    validator="material_coverage",
                    severity="warning",
                    message=(
                        f"Material failed conversion: {material.original_path}. "
                        f"Notes: {notes}"
                    ),
                    file_path=material.original_path,
                )
            )

    return issues


def validate_source_map(
    project_path: Path | str,
    state: ProjectState | None,
) -> list[ValidationIssue]:
    project_path = Path(project_path)
    source_map_path = project_path / "SOURCE_MAP.md"
    context_index_path = project_path / "CONTEXT_INDEX.md"
    issues: list[ValidationIssue] = []

    if not source_map_path.exists():
        return [
            ValidationIssue(
                validator="source_map",
                severity="error",
                message="SOURCE_MAP.md is missing.",
                file_path="SOURCE_MAP.md",
            )
        ]

    content = source_map_path.read_text(encoding="utf-8")
    if not content.strip():
        issues.append(
            ValidationIssue(
                validator="source_map",
                severity="error",
                message="SOURCE_MAP.md is empty.",
                file_path="SOURCE_MAP.md",
            )
        )

    if state is None:
        issues.append(
            ValidationIssue(
                validator="source_map",
                severity="info",
                message="Project state was not provided; material map checks were skipped.",
            )
        )
    else:
        for material in state.materials:
            if material.original_path and material.original_path not in content:
                issues.append(
                    ValidationIssue(
                        validator="source_map",
                        severity="warning",
                        message=(
                            "Material original path is missing from SOURCE_MAP.md: "
                            f"{material.original_path}"
                        ),
                        file_path="SOURCE_MAP.md",
                    )
                )

            if material.context_path and material.context_path not in content:
                issues.append(
                    ValidationIssue(
                        validator="source_map",
                        severity="warning",
                        message=(
                            "Material context path is missing from SOURCE_MAP.md: "
                            f"{material.context_path}"
                        ),
                        file_path="SOURCE_MAP.md",
                    )
                )

    for referenced_path in _referenced_workspace_paths(content):
        if not (project_path / referenced_path).exists():
            issues.append(
                ValidationIssue(
                    validator="source_map",
                    severity="error",
                    message=f"SOURCE_MAP.md references missing file: {referenced_path}",
                    file_path="SOURCE_MAP.md",
                )
            )

    if not context_index_path.exists():
        issues.append(
            ValidationIssue(
                validator="source_map",
                severity="warning",
                message="CONTEXT_INDEX.md is missing.",
                file_path="CONTEXT_INDEX.md",
            )
        )
    elif state is not None and state.materials:
        context_index = context_index_path.read_text(encoding="utf-8")
        missing_materials = []
        for material in state.materials:
            marker = material.context_path or material.source_id
            if marker and marker not in context_index:
                missing_materials.append(marker)

        if missing_materials:
            issues.append(
                ValidationIssue(
                    validator="source_map",
                    severity="warning",
                    message=(
                        "CONTEXT_INDEX.md does not reference all materials: "
                        + ", ".join(missing_materials)
                    ),
                    file_path="CONTEXT_INDEX.md",
                )
            )

    return issues


def validate_workspace_tree(project_path: Path | str) -> list[ValidationIssue]:
    project_path = Path(project_path)
    issues: list[ValidationIssue] = []

    canonical_files = [file_path for file_path, _purpose in CANONICAL_HANDOFF_FILES]
    for file_name in canonical_files:
        path = project_path / file_name
        if not path.exists():
            issues.append(
                ValidationIssue(
                    validator="workspace_tree",
                    severity="error",
                    message=f"Missing canonical file: {file_name}",
                    file_path=file_name,
                )
            )
        elif not path.read_text(encoding="utf-8").strip():
            issues.append(
                ValidationIssue(
                    validator="workspace_tree",
                    severity="warning",
                    message=f"Canonical file is empty: {file_name}",
                    file_path=file_name,
                )
            )

    for directory_name in CANONICAL_DIRECTORIES:
        if not (project_path / directory_name).is_dir():
            issues.append(
                ValidationIssue(
                    validator="workspace_tree",
                    severity="error",
                    message=f"Missing canonical directory: {directory_name}",
                    file_path=directory_name,
                )
            )

    if project_path.exists():
        for child in project_path.iterdir():
            if not re.match(r"^[a-zA-Z0-9_.-]+$", child.name):
                issues.append(
                    ValidationIssue(
                        validator="workspace_tree",
                        severity="warning",
                        message=f"Root name is not ASCII/tool safe: {child.name}",
                        file_path=child.name,
                    )
                )

    versions_dir = project_path / "_versions"
    if versions_dir.is_dir() and not _directory_has_content(versions_dir):
        issues.append(
            ValidationIssue(
                validator="workspace_tree",
                severity="info",
                message="_versions/ has no workspace snapshot yet.",
                file_path="_versions",
            )
        )

    return issues


def validate_handoff_anatomy(project_path: Path | str) -> list[ValidationIssue]:
    project_path = Path(project_path)
    issues: list[ValidationIssue] = []

    for section in validate_claude_md_anatomy(project_path):
        issues.append(
            ValidationIssue(
                validator="handoff_anatomy",
                severity="error",
                message=f"CLAUDE.md missing required section: {section}",
                file_path="CLAUDE.md",
            )
        )

    for section in validate_agents_md_anatomy(project_path):
        issues.append(
            ValidationIssue(
                validator="handoff_anatomy",
                severity="error",
                message=f"AGENTS.md missing required section: {section}",
                file_path="AGENTS.md",
            )
        )

    claude_path = project_path / "CLAUDE.md"
    if claude_path.exists():
        claude_md = claude_path.read_text(encoding="utf-8")
        for target in ["SOURCE_MAP.md", "CONTEXT_INDEX.md"]:
            if target not in claude_md:
                issues.append(
                    ValidationIssue(
                        validator="handoff_anatomy",
                        severity="warning",
                        message=f"CLAUDE.md does not reference {target}.",
                        file_path="CLAUDE.md",
                    )
                )

    agents_path = project_path / "AGENTS.md"
    if agents_path.exists():
        agents_md = agents_path.read_text(encoding="utf-8")
        if "NEXT_STEPS.md" not in agents_md:
            issues.append(
                ValidationIssue(
                    validator="handoff_anatomy",
                    severity="warning",
                    message="AGENTS.md does not reference NEXT_STEPS.md.",
                    file_path="AGENTS.md",
                )
            )

    return issues


def render_validation_report_markdown(report: ValidationReport) -> str:
    lines = [
        "# Validation Report",
        "",
        f"Timestamp: {report.timestamp}",
        "",
        "## Summary",
        "",
        (
            f"{report.error_count} errors, {report.warning_count} warnings, "
            f"{report.info_count} info"
        ),
        "",
        "## Validators Run",
        "",
        *[f"- {validator}" for validator in report.validators_run],
        "",
    ]

    for severity in ["error", "warning", "info"]:
        matching = [issue for issue in report.issues if issue.severity == severity]
        lines.extend([f"## {severity.title()}s", ""])
        if not matching:
            lines.append("- None.")
        else:
            for issue in matching:
                location = f" (`{issue.file_path}`)" if issue.file_path else ""
                lines.append(f"- **{issue.validator}**{location}: {issue.message}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_validation_report(
    project_path: Path | str,
    report: ValidationReport,
) -> tuple[Path, Path]:
    logs_dir = Path(project_path) / "_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = logs_dir / "validation_report.md"
    json_path = logs_dir / "validation_report.json"
    markdown_path.write_text(render_validation_report_markdown(report), encoding="utf-8")
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return markdown_path, json_path


def _count_by_severity(issues: list[ValidationIssue], severity: IssueSeverity) -> int:
    return len([issue for issue in issues if issue.severity == severity])


def _resolve_workspace_path(project_path: Path, file_path: str) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path
    return project_path / path


def _is_under_project(project_path: Path, file_path: Path) -> bool:
    try:
        file_path.resolve().relative_to(project_path.resolve())
    except ValueError:
        return False
    return True


def _without_markdown_heading(content: str, heading: str) -> str:
    pattern = re.compile(
        rf"^\s*#{{1,6}}\s*{re.escape(heading)}\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    return pattern.sub("", content).strip()


def _has_markdown_section(content: str, section: str) -> bool:
    pattern = re.compile(
        rf"^#{{1,6}}\s*(?:\d+\.\s*)?{re.escape(section)}\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    return bool(pattern.search(content))


def _gap_count_from_payload(payload: dict[str, object]) -> int | None:
    if isinstance(payload.get("gaps"), list):
        return len(payload["gaps"])

    keys = ["blockers", "assumptions", "optional_items"]
    if not any(key in payload for key in keys):
        return None

    count = 0
    for key in keys:
        value = payload.get(key, [])
        if isinstance(value, list):
            count += len(value)
    return count


def _directory_has_content(directory_path: Path) -> bool:
    if not directory_path.is_dir():
        return False
    return any(child.name != "README.md" for child in directory_path.iterdir())


def _referenced_workspace_paths(content: str) -> set[str]:
    references: set[str] = set()
    for match in re.finditer(r"`((?:_sources|_context)/[^`]+)`", content):
        references.add(_clean_reference(match.group(1)))

    for match in re.finditer(r"(?<![\w./-])((?:_sources|_context)/[^\s`|)]+)", content):
        references.add(_clean_reference(match.group(1)))

    return {reference for reference in references if reference}


def _clean_reference(reference: str) -> str:
    return reference.replace("\\", "/").strip().strip(".,;:")
