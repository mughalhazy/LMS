"""API schemas for lesson-service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import LessonStatus, LessonType


class LessonBase(BaseModel):
    course_id: str = Field(..., min_length=1)
    module_id: str | None = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    # CAT-018: closed enum per spec §3.1; default is "video" (most common type)
    lesson_type: LessonType = Field(default=LessonType.VIDEO)
    learning_objectives: list[str] = Field(default_factory=list)
    content_ref: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    availability_rules: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    order_index: int = Field(default=0, ge=0)


class LessonCreateRequest(LessonBase):
    """Payload for creating a lesson."""
    # CAT-019: spec §4.1 requires created_by in create request
    created_by: str = Field(default="system", min_length=1)


class LessonUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    lesson_type: str | None = Field(default=None, min_length=1)
    learning_objectives: list[str] | None = None
    content_ref: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    availability_rules: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    module_id: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class DeliveryStateUpdateRequest(BaseModel):
    state: dict[str, Any] = Field(default_factory=dict)


class ProgressionHookRequest(BaseModel):
    hook_type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)

    lesson_id: str
    tenant_id: str
    created_by: str
    status: LessonStatus
    delivery_state: dict[str, Any]
    version: int
    published_version: int | None
    published_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeliveryStateResponse(BaseModel):
    lesson_id: str
    course_id: str
    status: str
    launchable: bool
    blocked_reasons: list[str]
    availability_window: dict[str, str | None]
    requires_enrollment: bool
    prerequisite_state: dict[str, bool | list[str]]


class LessonListResponse(BaseModel):
    lessons: list[LessonResponse]


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    service_up: int
    lessons_total: int
    events_emitted: int


class LessonReorderRequest(BaseModel):
    ordered_lesson_ids: list[str] = Field(min_length=1)


class ErrorResponse(BaseModel):
    detail: str
