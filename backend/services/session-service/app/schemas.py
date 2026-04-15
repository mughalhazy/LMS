from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    tenant_id: str
    created_by: str
    title: str
    description: Optional[str] = None
    course_id: str
    lesson_id: Optional[str] = None
    cohort_ids: List[str] = Field(default_factory=list)
    delivery_mode: Literal["in_person", "online", "hybrid"]
    instructor_refs: List[str] = Field(default_factory=list)
    capacity: Optional[int] = None
    waitlist_enabled: bool = False
    delivery_metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateSessionRequest(BaseModel):
    tenant_id: str
    updated_by: str
    title: Optional[str] = None
    description: Optional[str] = None
    instructor_refs: Optional[List[str]] = None
    capacity: Optional[int] = None
    waitlist_enabled: Optional[bool] = None
    delivery_metadata: Optional[Dict[str, Any]] = None


class ScheduleSessionRequest(BaseModel):
    tenant_id: str
    scheduled_by: str
    timezone: str
    start_at: datetime
    end_at: datetime
    recurrence_rule: Optional[str] = None
    reason: str = "schedule update"
    force: bool = False


class TransitionRequest(BaseModel):
    tenant_id: str
    actor_id: str
    reason: Optional[str] = None


class LinkCourseRequest(BaseModel):
    tenant_id: str
    actor_id: str
    course_id: str


class LinkLessonRequest(BaseModel):
    tenant_id: str
    actor_id: str
    lesson_id: Optional[str] = None


class LinkCohortsRequest(BaseModel):
    tenant_id: str
    actor_id: str
    cohort_ids: List[str]
