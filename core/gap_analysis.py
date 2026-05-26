from __future__ import annotations

import hashlib
import re

from pydantic import BaseModel, Field

from amadeus.models.requirements import RequirementsModel
from amadeus.models.state import GapItem, ProjectPhase, ProjectState, ReadinessSnapshot

MATERIAL_HINT_PATTERNS = [
    r"\bpdf\b",
    r"\bdocx?\b",
    r"\bdatei(en)?\b",
    r"\bdokument(e|en)?\b",
    r"\bmaterial(ien)?\b",
    r"\banhang\b",
    r"\bupload\b",
    r"\bquelle(n)?\b",
    r"\battachment(s)?\b",
    r"\bfile(s)?\b",
]

OUTPUT_HINT_PATTERNS = [
    r"\bapp\b",
    r"\bapi\b",
    r"\bcode\b",
    r"\breport\b",
    r"\bbericht\b",
    r"\bdocument\b",
    r"\bdokument\b",
    r"\bdeck\b",
    r"\bslides?\b",
    r"\bwebsite\b",
    r"\btool\b",
    r"\bworkspace\b",
]


class GapAnalysisResult(BaseModel):
    blockers: list[GapItem] = Field(default_factory=list)
    assumptions: list[GapItem] = Field(default_factory=list)
    optional_items: list[GapItem] = Field(default_factory=list)
    missing_materials: list[str] = Field(default_factory=list)
    targeted_questions: list[str] = Field(default_factory=list)
    readiness_score: int = 0

    def all_gaps(self) -> list[GapItem]:
        return [*self.blockers, *self.assumptions, *self.optional_items]


class GapAnalyzer:
    """Deterministic gap analysis for the Amadeus readiness gate."""

    def analyze(
        self,
        requirements: RequirementsModel,
        state: ProjectState,
        raw_text: str,
    ) -> GapAnalysisResult:
        normalized_text = self._normalize(raw_text)
        result = GapAnalysisResult()

        if self._is_too_thin(raw_text, requirements):
            result.blockers.append(
                self._gap(
                    "blocker",
                    "Project goal needs more detail",
                    (
                        "The captured request is too short or generic for a reliable "
                        "handoff workspace."
                    ),
                    "What exactly should the executing agent deliver?",
                )
            )

        if self._mentions_materials(normalized_text) and not state.materials:
            result.blockers.append(
                self._gap(
                    "blocker",
                    "Referenced materials are missing",
                    (
                        "The input appears to reference files, documents, sources, or "
                        "attachments, but no material records are registered yet."
                    ),
                    "Which files or source materials should Amadeus ingest before build?",
                )
            )
            result.missing_materials.append("User-referenced files or source materials")

        failed_materials = [m for m in state.materials if m.status == "failed"]
        if failed_materials:
            for m in failed_materials:
                result.blockers.append(
                    self._gap(
                        "blocker",
                        f"Material extraction failed: {m.original_path}",
                        (
                            f"The provided material '{m.original_path}' could not be extracted: "
                            f"{'; '.join(m.extraction_notes)}"
                        ),
                        f"Can you provide '{m.original_path}' in a supported format (like .md or .txt)?",
                    )
                )

        if not state.materials:
            result.assumptions.append(
                self._gap(
                    "assumption",
                    "No external material supplied",
                    (
                        "The workspace will be built from the captured text only. "
                        "The executing agent must not assume additional source files exist."
                    ),
                    "Should any source files be added before the handoff is built?",
                    status="recorded",
                )
            )
        elif not self._mentions_materials(normalized_text):
            result.optional_items.append(
                self._gap(
                    "optional",
                    "Unreferenced materials attached",
                    (
                        "Source files were provided, but the input text does not explicitly "
                        "reference them. They will be included in the context anyway."
                    ),
                    "",
                )
            )

        if not self._has_output_hint(normalized_text, requirements):
            result.assumptions.append(
                self._gap(
                    "assumption",
                    "Final output format is not explicit",
                    (
                        "Amadeus captured a project goal, but the exact final output format "
                        "for the executing agent is not explicit."
                    ),
                    "What final artifact should the executing agent produce?",
                    status="recorded",
                )
            )

        if not requirements.quality_criteria:
            result.optional_items.append(
                self._gap(
                    "optional",
                    "No user-specific quality criteria captured",
                    (
                        "The handoff will use Amadeus defaults unless the user provides "
                        "project-specific quality rules."
                    ),
                    "Are there style, verification, or acceptance rules to add?",
                )
            )

        result.targeted_questions = [
            gap.question for gap in result.blockers + result.assumptions if gap.question
        ]
        result.readiness_score = self._score(result)
        return result

    def apply_to_state(self, state: ProjectState, result: GapAnalysisResult) -> ProjectState:
        state.gaps = result.all_gaps()
        state.open_questions = result.targeted_questions
        open_blockers = [
            gap.title
            for gap in result.blockers
            if gap.status not in {"resolved", "waived"}
        ]
        state.readiness = ReadinessSnapshot(
            score=result.readiness_score,
            can_build=not open_blockers,
            approval_required=bool(open_blockers),
            open_blockers=open_blockers,
            recorded_assumptions=[gap.title for gap in result.assumptions],
            optional_items=[gap.title for gap in result.optional_items],
            missing_materials=result.missing_materials,
        )
        state.transition_to(ProjectPhase.READINESS_REVIEW)
        return state

    def _is_too_thin(self, raw_text: str, requirements: RequirementsModel) -> bool:
        meaningful_words = re.findall(r"\b[\w-]{3,}\b", raw_text)
        if len(meaningful_words) < 5:
            return True

        description = requirements.short_description.strip().lower()
        generic_descriptions = {
            "prepare a handoff workspace.",
            "prepare a complete handoff workspace.",
            "ai handoff workspace",
        }
        return description in generic_descriptions

    def _mentions_materials(self, normalized_text: str) -> bool:
        return any(re.search(pattern, normalized_text) for pattern in MATERIAL_HINT_PATTERNS)

    def _has_output_hint(self, normalized_text: str, requirements: RequirementsModel) -> bool:
        if any(re.search(pattern, normalized_text) for pattern in OUTPUT_HINT_PATTERNS):
            return True
        joined_specs = self._normalize(" ".join(requirements.specifications))
        return any(re.search(pattern, joined_specs) for pattern in OUTPUT_HINT_PATTERNS)

    def _score(self, result: GapAnalysisResult) -> int:
        score = 100
        score -= len(result.blockers) * 35
        score -= len(result.assumptions) * 8
        score -= len(result.optional_items) * 3
        score -= len(result.missing_materials) * 10
        return max(0, min(100, score))

    def _gap(
        self,
        category: str,
        title: str,
        detail: str,
        question: str,
        status: str = "open",
    ) -> GapItem:
        return GapItem(
            gap_id=self._stable_id(category, title, detail),
            category=category,  # type: ignore[arg-type]
            title=title,
            detail=detail,
            question=question,
            status=status,  # type: ignore[arg-type]
        )

    def _stable_id(self, *parts: str) -> str:
        digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
        return f"gap-{digest}"

    def _normalize(self, text: str) -> str:
        return text.lower().strip()
