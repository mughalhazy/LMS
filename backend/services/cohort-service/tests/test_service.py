from datetime import datetime, timedelta

from src.repository import InMemoryCohortRepository
from src.service import CohortService, InvalidLifecycleTransitionError, TenantScopeError


def test_cohort_creation_and_lifecycle() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = service.create_cohort(
        tenant_id="tenant-a",
        program_id="program-1",
        cohort_name="Data Bootcamp",
        description="Intro cohort",
        start_date=datetime.utcnow() + timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        capacity=2,
        delivery_mode="instructor_led",
        timezone="UTC",
        facilitator_ids=["fac-1"],
    )

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

    try:
        service.transition_lifecycle(
            tenant_id="tenant-a",
            cohort_id=response["cohort_id"],
            target_status="scheduled",
            reason="should fail",
        )
        raised = False
    except InvalidLifecycleTransitionError:
        raised = True

    assert raised


def test_membership_capacity_and_tenant_scoping() -> None:
    service = CohortService(InMemoryCohortRepository())
    response = service.create_cohort(
        tenant_id="tenant-a",
        program_id="program-1",
        cohort_name="Capacity Cohort",
        description="cap",
        start_date=datetime.utcnow() + timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=3),
        capacity=1,
        delivery_mode="self_paced",
        timezone="UTC",
        facilitator_ids=["fac-1"],
    )

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

    try:
        service.list_tenant_cohorts("tenant-b")[0]
    except IndexError:
        pass

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
