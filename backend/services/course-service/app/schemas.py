from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"


class CourseBase(BaseModel):
    title: str | None = None
    description: str | None = None
    category_id: str | None = None
    language: str | None = None
    delivery_mode: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    tags: list[str] | None = None
    objectives: list[str] | None = None
    metadata: dict[str, Any] | None = None


class CreateCourseRequest(CourseBase):
    tenant_id: str
    created_by: str
    title: str


class UpdateCourseRequest(CourseBase):
    tenant_id: str
    updated_by: str


class PublishCourseRequest(BaseModel):
    tenant_id: str
    requested_by: str
    publish_notes: str | None = None
    scheduled_publish_at: datetime | None = None
    audience_rules: dict[str, Any] | None = None


class CreateCourseVersionRequest(BaseModel):
    tenant_id: str
    based_on_version: int
    created_by: str
    change_summary: str
    cloned_content_refs: list[str] | None = None
    metadata_overrides: dict[str, Any] | None = None


class CourseResponse(BaseModel):
    course_id: str
    tenant_id: str
    status: CourseStatus
    version: int
    created_at: datetime
    updated_at: datetime
    published_version: int | None = None
    published_at: datetime | None = None
    effective_from: datetime | None = None
    title: str
    description: str | None = None
    category_id: str | None = None
    language: str | None = None
    delivery_mode: str | None = None
    duration_minutes: int | None = None
    tags: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionResponse(BaseModel):
    course_id: str
    version_id: str
    new_version: int
    status: CourseStatus
    created_at: datetime
