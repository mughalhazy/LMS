from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PublishStatus(str, Enum):
    UNPUBLISHED = "unpublished"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class DeliveryRole(str, Enum):
    DEFAULT = "default"
    ALTERNATE = "alternate"
    REMEDIAL = "remedial"


class CourseMetadata(BaseModel):
    category_id: str | None = None
    delivery_mode: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    audience: str = "general"
    mandatory_training: bool = False
    compliance_policy_id: str | None = None
    renewal_cycle_days: int | None = Field(default=None, ge=1)
    manager_visibility_enabled: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_workforce_fields(self) -> "CourseMetadata":
        if self.mandatory_training and self.audience == "workforce" and not self.compliance_policy_id:
            raise ValueError("compliance_policy_id is required for workforce mandatory training")
        return self


class ProgramLink(BaseModel):
    program_id: str
    is_primary: bool = False


class SessionLink(BaseModel):
    session_id: str
    delivery_role: DeliveryRole = DeliveryRole.DEFAULT




class TenantContext(BaseModel):
    tenant_id: str
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)

class CreateCourseRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    created_by: str
    title: str
    institution_id: str | None = None
    course_code: str | None = None
    description: str | None = None
    language_code: str | None = None
    credit_value: float | None = None
    grading_scheme: str | None = None
    metadata: CourseMetadata = Field(default_factory=CourseMetadata)


class UpdateCourseRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    updated_by: str
    title: str | None = None
    course_code: str | None = None
    description: str | None = None
    language_code: str | None = None
    credit_value: float | None = None
    grading_scheme: str | None = None
    metadata: CourseMetadata | None = None


class PublishCourseRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    requested_by: str
    publish_notes: str | None = None
    scheduled_publish_at: datetime | None = None
    publish_mode: str = "immediate"


class ArchiveCourseRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    requested_by: str


class UpsertProgramLinksRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    updated_by: str
    program_links: list[ProgramLink]

    @model_validator(mode="after")
    def validate_single_primary(self) -> UpsertProgramLinksRequest:
        primary_count = len([link for link in self.program_links if link.is_primary])
        if primary_count > 1:
            raise ValueError("Only one primary program link is allowed")
        return self


class UpsertSessionLinksRequest(BaseModel):
    tenant_name: str = "tenant"
    country_code: str = "US"
    segment_type: str = "enterprise"
    plan_type: str = "free"
    addon_flags: list[str] = Field(default_factory=list)
    tenant_id: str
    updated_by: str
    session_links: list[SessionLink]


class CourseResponse(BaseModel):
    course_id: str
    tenant_id: str
    institution_id: str | None = None
    status: CourseStatus
    publish_status: PublishStatus
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    published_by: str | None = None
    course_code: str | None = None
    title: str
    description: str | None = None
    language_code: str | None = None
    credit_value: float | None = None
    grading_scheme: str | None = None
    metadata: CourseMetadata = Field(default_factory=CourseMetadata)
    program_links: list[ProgramLink] = Field(default_factory=list)
    session_links: list[SessionLink] = Field(default_factory=list)


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiMeta(BaseModel):
    request_id: str
    tenant_id: str
    timestamp: datetime


class ApiResponse(BaseModel):
    data: Any
    meta: ApiMeta
    errors: list[dict[str, Any]] = Field(default_factory=list)
