from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import Enrollment, EnrollmentMode, EnrollmentRequest, EnrollmentRuleSet, EnrollmentStatus


class EnrollmentServiceError(Exception):
    """Base error for enrollment service operations."""


class ValidationError(EnrollmentServiceError):
    """Raised when enrollment rules are violated."""


class NotFoundError(EnrollmentServiceError):
    """Raised when a requested enrollment does not exist."""


class EnrollmentService:
    """In-memory enrollment lifecycle service for courses or learning paths."""

    def __init__(self) -> None:
        self._rules_by_learning_object: Dict[str, EnrollmentRuleSet] = {}
        self._enrollments_by_id: Dict[str, Enrollment] = {}
        self._active_enrollment_by_pair: Dict[tuple[str, str], str] = {}
        self._active_enrollment_count: Dict[str, int] = defaultdict(int)

    def set_enrollment_rules(self, *, learning_object_id: str, rules: EnrollmentRuleSet) -> None:
        self._rules_by_learning_object[learning_object_id] = rules

    def enroll_learner(self, request: EnrollmentRequest) -> Enrollment:
        key = (request.learner_id, request.learning_object_id)
        if key in self._active_enrollment_by_pair:
            raise ValidationError("learner already has an active enrollment for this learning object")

        rules = self._rules_by_learning_object.get(request.learning_object_id, EnrollmentRuleSet())
        self._validate_request_rules(request=request, rules=rules)

        status = self._compute_initial_status(request=request, rules=rules)

        enrollment = Enrollment(
            tenant_id=request.tenant_id,
            organization_id=request.organization_id,
            learner_id=request.learner_id,
            learning_object_id=request.learning_object_id,
            status=status,
            requested_by=request.requested_by,
            mode=request.mode,
        )
        self._enrollments_by_id[enrollment.enrollment_id] = enrollment
        self._active_enrollment_by_pair[key] = enrollment.enrollment_id

        if enrollment.status == EnrollmentStatus.ENROLLED:
            self._active_enrollment_count[request.learning_object_id] += 1

        return enrollment

    def on_enrollment_created(self, request: EnrollmentRequest) -> Enrollment:
        """Create enrollment from an enrollment-created lifecycle event."""
        return self.enroll_learner(request)

    def on_learning_started(self, *, enrollment_id: str) -> Enrollment:
        """Mark an enrolled learner as actively learning (event-driven no-op in this bounded context)."""
        enrollment = self.get_enrollment_status(enrollment_id)
        if enrollment.status != EnrollmentStatus.ENROLLED:
            raise ValidationError("learning can only start from enrolled status")
        return enrollment

    def unenroll_learner(self, *, enrollment_id: str, actor_id: str) -> Enrollment:
        enrollment = self.get_enrollment_status(enrollment_id)
        if enrollment.status == EnrollmentStatus.UNENROLLED:
            raise ValidationError("enrollment is already unenrolled")

        prior_status = enrollment.status
        enrollment.mark_status(EnrollmentStatus.UNENROLLED)

        key = (enrollment.learner_id, enrollment.learning_object_id)
        self._active_enrollment_by_pair.pop(key, None)

        if prior_status == EnrollmentStatus.ENROLLED:
            self._active_enrollment_count[enrollment.learning_object_id] = max(
                0,
                self._active_enrollment_count[enrollment.learning_object_id] - 1,
            )

        return enrollment

    def get_enrollment_status(self, enrollment_id: str) -> Enrollment:
        enrollment = self._enrollments_by_id.get(enrollment_id)
        if not enrollment:
            raise NotFoundError(f"enrollment '{enrollment_id}' was not found")
        return enrollment

    def list_learner_enrollments(self, *, learner_id: str) -> List[Enrollment]:
        return [e for e in self._enrollments_by_id.values() if e.learner_id == learner_id]

    def _validate_request_rules(self, *, request: EnrollmentRequest, rules: EnrollmentRuleSet) -> None:
        if request.mode == EnrollmentMode.SELF and not rules.allow_self_enrollment:
            raise ValidationError("self-enrollment is disabled for this learning object")

        if rules.enforce_prerequisites and not request.prerequisite_satisfied:
            raise ValidationError("prerequisites are not satisfied for enrollment")

    def _compute_initial_status(self, *, request: EnrollmentRequest, rules: EnrollmentRuleSet) -> EnrollmentStatus:
        if rules.require_manager_approval and request.mode == EnrollmentMode.SELF:
            return EnrollmentStatus.PENDING_APPROVAL

        max_enrollments = rules.max_enrollments
        current_enrollments = self._active_enrollment_count[request.learning_object_id]
        if max_enrollments is not None and current_enrollments >= max_enrollments:
            if rules.allow_waitlist:
                return EnrollmentStatus.WAITLISTED
            raise ValidationError("capacity reached and waitlist is disabled")

        return EnrollmentStatus.ENROLLED
