"""API schemas for lesson-service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import LessonStatus


class LessonBase(BaseModel):
    course_id: str = Field(..., min_length=1)
    module_id: str | None = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    lesson_type: str = Field(default="self_paced", min_length=1)
    learning_objectives: list[str] = Field(default_factory=list)
    content_ref: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    availability_rules: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    order_index: int = Field(default=0, ge=0)


class LessonCreateRequest(LessonBase):
    pass


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


class ErrorResponse(BaseModel):
    detail: str
