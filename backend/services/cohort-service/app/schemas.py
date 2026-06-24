from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    # B11-001: cohort-batch-schema.md §3.3 batch_state values
    OPEN = "open"
    RUNNING = "running"
    ENDED = "ended"
    CLOSED = "closed"


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
    # B11-001: cohort-batch-schema.md §3.3 — Batch-specific fields
    delivery_pattern: str | None = None  # weekday|weekend|intensive|self_paced_assisted
    seat_limit: int | None = None
    # B11-002: cohort-batch-schema.md §3.4 — SessionGroup-specific fields
    max_size: int | None = None
    lead_tutor_id: str | None = None


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
    # G-21: LearningGroup compatibility aliases (spec uses group_id / group_type)
    group_id: str = ""
    group_type: str = ""
    # B11-001: cohort-batch-schema.md §3.3 — Batch-specific fields
    delivery_pattern: str | None = None
    seat_limit: int | None = None
    # B11-002: cohort-batch-schema.md §3.4 — SessionGroup-specific fields
    max_size: int | None = None
    lead_tutor_id: str | None = None

    @model_validator(mode="after")
    def _set_group_aliases(self) -> "CohortResponse":
        if not self.group_id:
            self.group_id = self.cohort_id
        if not self.group_type:
            self.group_type = self.kind.value if hasattr(self.kind, "value") else str(self.kind)
        return self


class CohortWithMembershipsResponse(BaseModel):
    cohort: CohortResponse
    memberships: list[MembershipResponse]


class BulkCreateCohortsRequest(BaseModel):
    cohorts: list[CreateCohortRequest] = Field(min_length=1)


class BulkStatusUpdateRequest(BaseModel):
    cohort_ids: list[str] = Field(min_length=1)
    status: CohortStatus
    updated_by: str = Field(min_length=1)


class BulkCohortResult(BaseModel):
    cohort_id: str | None = None
    status: str
    error: str | None = None


class BulkCohortResponse(BaseModel):
    results: list[BulkCohortResult]
    succeeded: int
    failed: int


class UpdateMembershipRequest(BaseModel):
    role: str | None = Field(default=None, min_length=2, max_length=64)
    updated_by: str = Field(min_length=1)


class ProgramLinkResponse(BaseModel):
    link_id: str
    cohort_id: str
    program_id: str
    linked_by: str
    linked_at: datetime


class UpdateProgramLinkRequest(BaseModel):
    program_id: str = Field(min_length=1)
    updated_by: str = Field(min_length=1)


class StatusHistoryEntry(BaseModel):
    status: CohortStatus
    changed_at: datetime
    changed_by: str


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    counters: dict[str, int]
