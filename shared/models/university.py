from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ProgramCourseRule:
    course_id: str
    sequence_order: int
    prerequisite_course_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssessmentProgressStep:
    assessment_id: str
    passed: bool
    score_percent: float
    attempted_at: datetime


@dataclass(slots=True)
class UniversityCompletionPayload:
    tenant_id: str
    user_id: str
    course_id: str
    program_id: str | None
    completed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


def prerequisite_ids_from_rule(rule: dict[str, Any] | None) -> list[str]:
    if not rule:
        return []
    prereqs = rule.get("prerequisite_course_ids", [])
    return [str(item) for item in prereqs if str(item).strip()]
