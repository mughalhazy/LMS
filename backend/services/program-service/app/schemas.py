from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import LinkStatus, ProgramStatus, ProgramVisibility


class ProgramCourseInput(BaseModel):
    course_id: str
    sequence_order: int = Field(ge=1)
    is_required: bool
    minimum_completion_pct: int | None = Field(default=None, ge=0, le=100)
    availability_rule: dict[str, Any] | None = None


class CreateProgramRequest(BaseModel):
    tenant_id: str
    institution_id: str
    code: str
    title: str
    description: str | None = None
    visibility: ProgramVisibility = ProgramVisibility.PRIVATE
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str


class ProgramResponse(BaseModel):
    program_id: str
    tenant_id: str
    institution_id: str
    code: str
    title: str
    description: str | None = None
    status: ProgramStatus
    version: int
    visibility: ProgramVisibility
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    mapping_version: int
    created_at: datetime
    updated_at: datetime


class ProgramListResponse(BaseModel):
    items: list[ProgramResponse]
    page: int
    page_size: int
    total: int


class UpdateProgramRequest(BaseModel):
    tenant_id: str
    title: str | None = None
    description: str | None = None
    visibility: ProgramVisibility | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict[str, Any] | None = None
    updated_by: str


class ProgramUpdateResult(BaseModel):
    program_id: str
    version: int
    status: ProgramStatus
    updated_fields: list[str]
    updated_at: datetime


class TransitionProgramStatusRequest(BaseModel):
    tenant_id: str
    target_status: ProgramStatus
    change_reason: str
    changed_by: str


class StatusTransitionResponse(BaseModel):
    program_id: str
    from_status: ProgramStatus
    to_status: ProgramStatus
    changed_at: datetime


class UpsertInstitutionLinkRequest(BaseModel):
    tenant_id: str
    institution_id: str
    link_status: LinkStatus
    link_metadata: dict[str, Any] = Field(default_factory=dict)
    updated_by: str


class InstitutionLinkResponse(BaseModel):
    program_id: str
    institution_id: str
    link_status: LinkStatus
    linked_at: datetime | None = None
    unlinked_at: datetime | None = None
    link_metadata: dict[str, Any] = Field(default_factory=dict)


class ReplaceProgramCoursesRequest(BaseModel):
    tenant_id: str
    updated_by: str
    courses: list[ProgramCourseInput]


class ProgramCourseResponse(BaseModel):
    course_id: str
    sequence_order: int
    is_required: bool
    minimum_completion_pct: int | None = None


class ProgramCoursesMapResponse(BaseModel):
    program_id: str
    mapping_version: int
    mapped_courses: list[ProgramCourseResponse]
    updated_at: datetime


class ProgramDetailResponse(BaseModel):
    program: ProgramResponse
    institution_link: InstitutionLinkResponse | None = None
    mapped_courses: list[ProgramCourseResponse]
    status_history: list[StatusTransitionResponse]
