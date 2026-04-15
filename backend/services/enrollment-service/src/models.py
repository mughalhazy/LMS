from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class EnrollmentStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    ENROLLED = "enrolled"
    WAITLISTED = "waitlisted"
    UNENROLLED = "unenrolled"


class EnrollmentMode(str, Enum):
    SELF = "self"
    MANAGER = "manager"
    ADMIN = "admin"
    AUTO = "auto"


@dataclass
class EnrollmentRuleSet:
    allow_self_enrollment: bool = True
    require_manager_approval: bool = False
    max_enrollments: Optional[int] = None
    allow_waitlist: bool = True
    enforce_prerequisites: bool = False


@dataclass
class EnrollmentRequest:
    tenant_id: str
    organization_id: str
    learner_id: str
    learning_object_id: str
    requested_by: str
    mode: EnrollmentMode = EnrollmentMode.SELF
    prerequisite_satisfied: bool = True


@dataclass
class Enrollment:
    tenant_id: str
    organization_id: str
    learner_id: str
    learning_object_id: str
    status: EnrollmentStatus
    requested_by: str
    mode: EnrollmentMode
    enrollment_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    unenrolled_at: Optional[datetime] = None

    def mark_status(self, status: EnrollmentStatus) -> None:
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        if status == EnrollmentStatus.UNENROLLED:
            self.unenrolled_at = self.updated_at
