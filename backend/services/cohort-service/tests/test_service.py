from datetime import datetime, timedelta

from src.repository import InMemoryCohortRepository
from src.service import CohortService, CohortServiceError, InvalidLifecycleTransitionError, TenantScopeError


def _create_cohort(service: CohortService, *, tenant_id: str = "tenant-a", capacity: int = 2) -> dict:
    return service.create_cohort(
        tenant_id=tenant_id,
        program_id="program-1",
        cohort_name="Data Bootcamp",
        description="Intro cohort",
        start_date=datetime.utcnow() + timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        capacity=capacity,
        delivery_mode="instructor_led",
        timezone="UTC",
        facilitator_ids=["fac-1"],
    )


def test_cohort_creation_and_lifecycle() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = _create_cohort(service)

    assert response["cohort_status"] == "scheduled"

    active = service.transition_lifecycle(
        tenant_id="tenant-a",
        cohort_id=response["cohort_id"],
        target_status="active",
        reason="start date reached",
    )
    assert active["cohort_status"] == "active"


def test_invalid_lifecycle_transition_rejected() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = service.create_cohort(
        tenant_id="tenant-a",
        program_id="program-1",
        cohort_name="Quick Cohort",
        description="Now",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=1),
        capacity=1,
        delivery_mode="blended",
        timezone="UTC",
        facilitator_ids=["fac-1"],
    )

    raised = False
    try:
        service.transition_lifecycle(
            tenant_id="tenant-a",
            cohort_id=response["cohort_id"],
            target_status="scheduled",
            reason="should fail",
        )
    except InvalidLifecycleTransitionError:
        raised = True

    assert raised


def test_membership_capacity_tenant_scoping_and_waitlist_promotion() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = _create_cohort(service, capacity=1)

    assign = service.assign_members(
        tenant_id="tenant-a",
        cohort_id=response["cohort_id"],
        assignment_mode="manual",
        learner_ids=["u1", "u2"],
        assigned_by="admin",
        effective_date=datetime.utcnow(),
    )

    assert assign["assignment_summary"]["assigned"] == 2
    assert len(assign["waitlist_entries"]) == 1

    removed = service.remove_member(
        tenant_id="tenant-a",
        cohort_id=response["cohort_id"],
        learner_id="u1",
        removed_by="admin",
    )
    assert removed["state"] == "removed"

    memberships = service.repository.list_memberships(response["cohort_id"])
    promoted = [m for m in memberships if m.learner_id == "u2"][0]
    assert promoted.state.value == "active"

    raised = False
    try:
        service.assign_members(
            tenant_id="tenant-b",
            cohort_id=response["cohort_id"],
            assignment_mode="manual",
            learner_ids=["u3"],
            assigned_by="admin",
            effective_date=datetime.utcnow(),
        )
    except TenantScopeError:
        raised = True

    assert raised


def test_schedule_management_publishes_calendar() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = _create_cohort(service)
    now = datetime.utcnow() + timedelta(days=2)

    schedule = service.update_schedule(
        tenant_id="tenant-a",
        cohort_id=response["cohort_id"],
        session_plan=[
            {
                "session_id": "s1",
                "title": "Kickoff",
                "start_at": now,
                "end_at": now + timedelta(hours=2),
                "instructor_id": "inst-1",
                "modality": "virtual",
            }
        ],
        milestone_dates={
            "enrollment_cutoff": now - timedelta(days=1),
            "assignment_due_dates": {"assignment-1": now + timedelta(days=5)},
            "assessments": {"assessment-1": now + timedelta(days=10)},
        },
        recurrence_rules={"freq": "weekly"},
        holiday_blackouts=["2026-12-25"],
        update_reason="initial planning",
    )

    assert schedule["audit_event"] == "CohortScheduleUpdated"
    assert schedule["schedule_version"] == 1
    assert len(schedule["published_cohort_calendar"]["session_plan"]) == 1


def test_schedule_rejects_invalid_session_window() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = _create_cohort(service)
    start = datetime.utcnow() + timedelta(days=60)

    try:
        service.update_schedule(
            tenant_id="tenant-a",
            cohort_id=response["cohort_id"],
            session_plan=[
                {
                    "session_id": "outside-window",
                    "title": "Late Session",
                    "start_at": start,
                    "end_at": start + timedelta(hours=2),
                    "instructor_id": "inst-1",
                    "modality": "virtual",
                }
            ],
            update_reason="invalid",
        )
        raised = False
    except CohortServiceError:
        raised = True

    assert raised
