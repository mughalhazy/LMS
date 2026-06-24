"""Domain models for the enrollment service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EnrollmentStatus(str, Enum):
    ASSIGNED = "assigned"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"
    EXPIRED = "expired"          # Assignment deadline passed before learner activated


TERMINAL_STATUSES = {
    EnrollmentStatus.COMPLETED,
    EnrollmentStatus.WITHDRAWN,
    EnrollmentStatus.CANCELLED,
    EnrollmentStatus.EXPIRED,
}


ALLOWED_TRANSITIONS: dict[EnrollmentStatus, set[EnrollmentStatus]] = {
    EnrollmentStatus.ASSIGNED: {EnrollmentStatus.ACTIVE, EnrollmentStatus.CANCELLED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.EXPIRED},
    EnrollmentStatus.ACTIVE: {EnrollmentStatus.COMPLETED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.CANCELLED, EnrollmentStatus.EXPIRED},
    EnrollmentStatus.COMPLETED: set(),
    EnrollmentStatus.WITHDRAWN: set(),
    EnrollmentStatus.CANCELLED: set(),
    EnrollmentStatus.EXPIRED: set(),
}


@dataclass(slots=True)
class Enrollment:
    tenant_id: str
    learner_id: str
    course_id: str
    assigned_by: str
    assignment_source: str
    cohort_id: str | None = None
    session_id: str | None = None
    course_title: str | None = None
    status: EnrollmentStatus = EnrollmentStatus.ASSIGNED
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enrolled_at: datetime | None = None
    completed_at: datetime | None = None
    dropped_at: datetime | None = None
    deferred_at: datetime | None = None
    expired_at: datetime | None = None

    def transition_to(self, to_status: EnrollmentStatus) -> None:
        if to_status == self.status:
            return
        allowed = ALLOWED_TRANSITIONS[self.status]
        if to_status not in allowed:
            raise ValueError(f"invalid transition from {self.status.value} to {to_status.value}")
        self.status = to_status
        now = datetime.now(timezone.utc)
        self.updated_at = now
        _stamps = {
            EnrollmentStatus.ACTIVE: "enrolled_at",
            EnrollmentStatus.COMPLETED: "completed_at",
            EnrollmentStatus.WITHDRAWN: "dropped_at",
            EnrollmentStatus.CANCELLED: "dropped_at",
            EnrollmentStatus.EXPIRED: "expired_at",
        }
        attr = _stamps.get(to_status)
        if attr and getattr(self, attr) is None:
            object.__setattr__(self, attr, now)


@dataclass(slots=True)
class AuditLogEntry:
    tenant_id: str
    actor_id: str
    action: str
    enrollment_id: str
    metadata: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Event:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TenantContext:
    tenant_id: str
    actor_id: str
