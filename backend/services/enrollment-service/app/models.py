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


TERMINAL_STATUSES = {EnrollmentStatus.COMPLETED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.CANCELLED}


ALLOWED_TRANSITIONS: dict[EnrollmentStatus, set[EnrollmentStatus]] = {
    EnrollmentStatus.ASSIGNED: {EnrollmentStatus.ACTIVE, EnrollmentStatus.CANCELLED, EnrollmentStatus.WITHDRAWN},
    EnrollmentStatus.ACTIVE: {EnrollmentStatus.COMPLETED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.CANCELLED},
    EnrollmentStatus.COMPLETED: set(),
    EnrollmentStatus.WITHDRAWN: set(),
    EnrollmentStatus.CANCELLED: set(),
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
    status: EnrollmentStatus = EnrollmentStatus.ASSIGNED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def transition_to(self, to_status: EnrollmentStatus) -> None:
        if to_status == self.status:
            return
        allowed = ALLOWED_TRANSITIONS[self.status]
        if to_status not in allowed:
            raise ValueError(f"invalid transition from {self.status.value} to {to_status.value}")
        self.status = to_status
        self.updated_at = datetime.now(timezone.utc)


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
    name: str
    tenant_id: str
    enrollment_id: str
    payload: dict[str, Any]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class TenantContext:
    tenant_id: str
    actor_id: str
