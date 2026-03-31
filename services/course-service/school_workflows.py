from __future__ import annotations

from dataclasses import dataclass, field

from shared.models.school import StudentGuardianLink


@dataclass
class SchoolCourseRoster:
    """School-specific roster projection used by existing course domain logic."""

    course_id: str
    student_ids: set[str] = field(default_factory=set)
    guardian_links: dict[str, set[str]] = field(default_factory=dict)

    def enroll_student(self, student_id: str) -> None:
        self.student_ids.add(student_id)

    def add_guardian_link(self, link: StudentGuardianLink) -> None:
        if link.student_id not in self.student_ids:
            raise ValueError(f"student {link.student_id} is not enrolled in course {self.course_id}")
        self.guardian_links.setdefault(link.student_id, set()).add(link.guardian_id)

    def guardians_for_student(self, student_id: str) -> list[str]:
        return sorted(self.guardian_links.get(student_id, set()))
