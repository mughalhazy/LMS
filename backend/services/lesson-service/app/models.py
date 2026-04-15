"""Domain models for lesson-service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class LessonStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LifecycleAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    UNPUBLISH = "unpublish"
    DELETE = "delete"
    DELIVERY_STATE = "delivery_state"
    PROGRESSION_HOOK = "progression_hook"


@dataclass
class Lesson:
    tenant_id: str
    course_id: str
    title: str
    created_by: str
    lesson_type: str = "self_paced"
    description: str | None = None
    module_id: str | None = None
    learning_objectives: list[str] = field(default_factory=list)
    content_ref: str | None = None
    estimated_duration_minutes: int | None = None
    availability_rules: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    delivery_state: dict[str, Any] = field(default_factory=dict)
    order_index: int = 0
    lesson_id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    published_version: int | None = None
    status: LessonStatus = LessonStatus.DRAFT
    published_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AuditRecord:
    tenant_id: str
    actor_id: str
    lesson_id: str
    action: LifecycleAction
    detail: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OutboxEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
