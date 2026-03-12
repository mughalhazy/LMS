from src.models import EnrollmentMode, EnrollmentRequest, EnrollmentRuleSet, EnrollmentStatus
from src.service import EnrollmentService, NotFoundError, ValidationError


def _request(**overrides):
    payload = {
        "tenant_id": "tenant-1",
        "organization_id": "org-1",
        "learner_id": "learner-1",
        "learning_object_id": "course-1",
        "requested_by": "learner-1",
        "mode": EnrollmentMode.SELF,
        "prerequisite_satisfied": True,
    }
    payload.update(overrides)
    return EnrollmentRequest(**payload)


def test_enroll_and_get_status():
    service = EnrollmentService()

    enrollment = service.enroll_learner(_request())

    assert enrollment.status == EnrollmentStatus.ENROLLED
    assert service.get_enrollment_status(enrollment.enrollment_id).status == EnrollmentStatus.ENROLLED


def test_unenroll_changes_status_and_allows_reenrollment():
    service = EnrollmentService()
    enrollment = service.enroll_learner(_request())

    updated = service.unenroll_learner(enrollment_id=enrollment.enrollment_id, actor_id="admin-1")
    assert updated.status == EnrollmentStatus.UNENROLLED

    second_enrollment = service.enroll_learner(_request())
    assert second_enrollment.status == EnrollmentStatus.ENROLLED


def test_enrollment_rules_apply_for_approval_capacity_and_prerequisites():
    service = EnrollmentService()
    service.set_enrollment_rules(
        learning_object_id="course-1",
        rules=EnrollmentRuleSet(
            allow_self_enrollment=True,
            require_manager_approval=True,
            max_enrollments=1,
            allow_waitlist=True,
            enforce_prerequisites=True,
        ),
    )

    pending = service.enroll_learner(_request(learner_id="learner-2"))
    assert pending.status == EnrollmentStatus.PENDING_APPROVAL

    approved_by_admin = service.enroll_learner(
        _request(learner_id="learner-3", requested_by="admin-1", mode=EnrollmentMode.ADMIN)
    )
    assert approved_by_admin.status == EnrollmentStatus.ENROLLED

    waitlisted = service.enroll_learner(
        _request(learner_id="learner-4", requested_by="admin-1", mode=EnrollmentMode.ADMIN)
    )
    assert waitlisted.status == EnrollmentStatus.WAITLISTED

    try:
        service.enroll_learner(
            _request(learner_id="learner-5", prerequisite_satisfied=False, mode=EnrollmentMode.ADMIN)
        )
    except ValidationError as error:
        assert "prerequisites" in str(error)
    else:
        raise AssertionError("Expected ValidationError")


def test_self_enrollment_disabled_and_not_found_errors():
    service = EnrollmentService()
    service.set_enrollment_rules(
        learning_object_id="course-1",
        rules=EnrollmentRuleSet(allow_self_enrollment=False),
    )

    try:
        service.enroll_learner(_request())
    except ValidationError as error:
        assert "self-enrollment" in str(error)
    else:
        raise AssertionError("Expected ValidationError")

    try:
        service.get_enrollment_status("missing")
    except NotFoundError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("Expected NotFoundError")
