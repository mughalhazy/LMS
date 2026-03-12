from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .repository import InMemoryCohortRepository
from .service import CohortService

repository = InMemoryCohortRepository()
service = CohortService(repository)


class CohortCreateRequest(BaseModel):
    tenant_id: str
    program_id: str
    cohort_name: str
    description: str
    start_date: datetime
    end_date: datetime
    capacity: int = Field(ge=1)
    delivery_mode: str
    timezone: str
    facilitator_ids: List[str]
    enrollment_rules: Optional[Dict] = None
    metadata: Optional[Dict[str, str]] = None


class LifecycleTransitionRequest(BaseModel):
    tenant_id: str
    target_status: str
    reason: str


class MembershipAssignRequest(BaseModel):
    tenant_id: str
    assignment_mode: str
    learner_ids: List[str]
    assigned_by: str
    effective_date: datetime
    override_flags: Optional[Dict[str, bool]] = None


class MembershipRemoveRequest(BaseModel):
    tenant_id: str
    learner_id: str
    removed_by: str


class ScheduleManagementRequest(BaseModel):
    tenant_id: str
    session_plan: List[Dict]
    milestone_dates: Optional[Dict] = None
    recurrence_rules: Optional[Dict] = None
    holiday_blackouts: Optional[List[str]] = None
    update_reason: str


# Endpoint handlers designed for framework adapters

def create_cohort(payload: CohortCreateRequest) -> Dict:
    return service.create_cohort(**payload.model_dump())


def transition_cohort_lifecycle(cohort_id: str, payload: LifecycleTransitionRequest) -> Dict:
    return service.transition_lifecycle(cohort_id=cohort_id, **payload.model_dump())


def assign_cohort_members(cohort_id: str, payload: MembershipAssignRequest) -> Dict:
    return service.assign_members(cohort_id=cohort_id, **payload.model_dump())


def remove_cohort_member(cohort_id: str, payload: MembershipRemoveRequest) -> Dict:
    return service.remove_member(cohort_id=cohort_id, **payload.model_dump())


def list_cohorts(tenant_id: str) -> List[Dict]:
    return service.list_tenant_cohorts(tenant_id=tenant_id)


def update_cohort_schedule(cohort_id: str, payload: ScheduleManagementRequest) -> Dict:
    return service.update_schedule(cohort_id=cohort_id, **payload.model_dump())
