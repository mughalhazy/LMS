from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Sequence, Set

from .models import (
    CoursePrerequisiteRule,
    EnrollmentDecision,
    EquivalencyMapping,
    PrerequisiteEvaluationResult,
    PrerequisiteNode,
    TranscriptIndex,
    TranscriptRecord,
)


class CoursePrerequisiteValidator:
    """
    Validates course prerequisites against learner transcript records, supporting:
    - AND/OR prerequisite node evaluation
    - course equivalency mappings
    - minimum grade and validity windows
    """

    @staticmethod
    def _build_transcript_index(transcript: Sequence[TranscriptRecord]) -> TranscriptIndex:
        index: TranscriptIndex = defaultdict(list)
        for record in transcript:
            index[record.course_id].append(record)
        return index

    @staticmethod
    def _resolve_equivalents(course_id: str, mappings: Sequence[EquivalencyMapping]) -> Set[str]:
        equivalents: Set[str] = {course_id}
        for mapping in mappings:
            if mapping.source_course_id == course_id:
                equivalents.update(mapping.equivalent_course_ids)
            if course_id in mapping.equivalent_course_ids:
                equivalents.add(mapping.source_course_id)
                equivalents.update(mapping.equivalent_course_ids)
        return equivalents

    @staticmethod
    def _record_satisfies(record: TranscriptRecord, node: PrerequisiteNode, now: datetime) -> bool:
        if record.completion_status.lower() != "completed":
            return False

        if node.minimum_grade is not None:
            if record.score is None or record.score < node.minimum_grade:
                return False

        if node.valid_for_days is not None:
            if record.completed_at is None:
                return False
            if record.completed_at < now - timedelta(days=node.valid_for_days):
                return False

        return True

    @classmethod
    def _course_satisfied(
        cls,
        candidate_course_id: str,
        transcript_index: Dict[str, List[TranscriptRecord]],
        node: PrerequisiteNode,
        now: datetime,
    ) -> bool:
        records = transcript_index.get(candidate_course_id, [])
        return any(cls._record_satisfies(record, node, now) for record in records)

    @classmethod
    def _node_satisfied(
        cls,
        node: PrerequisiteNode,
        transcript_index: Dict[str, List[TranscriptRecord]],
        equivalencies: Sequence[EquivalencyMapping],
        now: datetime,
    ) -> bool:
        required_courses = list(node.required_course_ids)
        candidate_sets = [cls._resolve_equivalents(course_id, equivalencies) for course_id in required_courses]

        if node.operator.upper() == "OR":
            for candidate_set in candidate_sets:
                if any(cls._course_satisfied(course_id, transcript_index, node, now) for course_id in candidate_set):
                    return True
            return False

        # Default to AND.
        for candidate_set in candidate_sets:
            if not any(cls._course_satisfied(course_id, transcript_index, node, now) for course_id in candidate_set):
                return False
        return True

    @classmethod
    def validate_enrollment_prerequisites(
        cls,
        rule: CoursePrerequisiteRule,
        transcript: Sequence[TranscriptRecord],
        equivalencies: Sequence[EquivalencyMapping],
        now: datetime | None = None,
    ) -> PrerequisiteEvaluationResult:
        now = now or datetime.utcnow()
        transcript_index = cls._build_transcript_index(transcript)

        unmet: List[str] = []
        recommendations: List[str] = []

        for node in rule.prerequisite_nodes:
            if not cls._node_satisfied(node, transcript_index, equivalencies, now):
                unmet.append(node.node_id)
                recommendations.extend(node.bridge_recommendations)

        decision = EnrollmentDecision.APPROVED if not unmet else EnrollmentDecision.BLOCKED
        return PrerequisiteEvaluationResult(
            enrollment_decision=decision,
            unmet_prerequisites=unmet,
            remedial_recommendations=sorted(set(recommendations)),
            evaluated_at=now,
        )
