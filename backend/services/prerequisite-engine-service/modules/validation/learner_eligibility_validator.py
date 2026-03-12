from __future__ import annotations

from typing import List

from .models import CourseCatalogEntry, EligibilityResult, LearnerProfile


class LearnerEligibilityValidator:
    """Validates if a learner is eligible to attempt enrollment for a course."""

    @staticmethod
    def validate(learner: LearnerProfile, course: CourseCatalogEntry) -> EligibilityResult:
        reasons: List[str] = []

        if learner.tenant_id != course.tenant_id:
            reasons.append("tenant_mismatch")

        if not learner.is_active:
            reasons.append("learner_inactive")

        if learner.compliance_hold:
            reasons.append("learner_compliance_hold")

        if course.status.lower() != "published":
            reasons.append("course_not_published")

        if course.audience_roles and not set(learner.roles).intersection(course.audience_roles):
            reasons.append("audience_role_restriction")

        if course.audience_departments and not set(learner.departments).intersection(course.audience_departments):
            reasons.append("audience_department_restriction")

        if course.audience_locations and not set(learner.locations).intersection(course.audience_locations):
            reasons.append("audience_location_restriction")

        return EligibilityResult(eligible=len(reasons) == 0, reasons=reasons)
