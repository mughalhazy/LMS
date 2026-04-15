from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CohortKind(str, Enum):
    FORMAL_COHORT = "formal_cohort"
    ACADEMY_BATCH = "academy_batch"
    TUTOR_GROUP = "tutor_group"


class CohortStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class CohortSchedule(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = "UTC"


class CreateCohortRequest(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    code: str = Field(min_length=2, max_length=64)
    kind: CohortKind
    program_id: str | None = None
    status: CohortStatus = CohortStatus.DRAFT
    schedule: CohortSchedule = Field(default_factory=CohortSchedule)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_by: str = Field(min_length=1)


class UpdateCohortRequest(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    program_id: str | None = None
    status: CohortStatus | None = None
    schedule: CohortSchedule | None = None
    metadata: dict[str, str] | None = None
    updated_by: str = Field(min_length=1)


class LinkProgramRequest(BaseModel):
    program_id: str = Field(min_length=1)
    linked_by: str = Field(min_length=1)


class AddMembershipRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(min_length=2, max_length=64)
    joined_at: datetime | None = None
    added_by: str = Field(min_length=1)


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: str
    cohort_id: str
    user_id: str
    role: str
    joined_at: datetime
    added_by: str


class CohortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cohort_id: str
    tenant_id: str
    name: str
    code: str
    kind: CohortKind
    status: CohortStatus
    schedule: CohortSchedule
    program_id: str | None
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime
    created_by: str


class CohortWithMembershipsResponse(BaseModel):
    cohort: CohortResponse
    memberships: list[MembershipResponse]


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    counters: dict[str, int]
