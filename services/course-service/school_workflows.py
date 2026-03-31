from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from shared.models.school import StudentGuardianLink


@dataclass
class SegmentCourseRoster:
    """Config-driven roster projection without segment-specific branches."""

    course_id: str
    behavior_config: dict[str, bool] = field(default_factory=dict)
    student_ids: set[str] = field(default_factory=set)
    guardian_links: dict[str, set[str]] = field(default_factory=dict)
    cohort_members: dict[str, set[str]] = field(default_factory=dict)
    entitlement: Callable[[str], bool] = field(default=lambda _capability_id: True)

    def _is_behavior_enabled(self, key: str, *, default: bool = False) -> bool:
        return bool(self.behavior_config.get(key, default))

    def enroll_student(self, student_id: str) -> None:
        is_enabled = self.entitlement("course.roster.enroll")
        if not is_enabled:
            raise PermissionError("capability denied: course.roster.enroll")
        self.student_ids.add(student_id)

    def add_guardian_link(self, link: StudentGuardianLink) -> None:
        is_enabled = self.entitlement("course.roster.guardian_link.write")
        if not is_enabled:
            raise PermissionError("capability denied: course.roster.guardian_link.write")
        if link.student_id not in self.student_ids:
            raise ValueError(f"student {link.student_id} is not enrolled in course {self.course_id}")
        self.guardian_links.setdefault(link.student_id, set()).add(link.guardian_id)

    def assign_student_to_cohort(self, *, student_id: str, cohort_id: str) -> None:
        if not self._is_behavior_enabled("cohort_enabled"):
            raise RuntimeError("segment behavior disabled: cohort_enabled")
        if student_id not in self.student_ids:
            raise ValueError(f"student {student_id} is not enrolled in course {self.course_id}")
        self.cohort_members.setdefault(cohort_id, set()).add(student_id)

    def guardians_for_student(self, student_id: str) -> list[str]:
        return sorted(self.guardian_links.get(student_id, set()))


SchoolCourseRoster = SegmentCourseRoster
