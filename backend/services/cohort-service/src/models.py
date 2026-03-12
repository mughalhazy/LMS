from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class CohortStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DeliveryMode(str, Enum):
    SELF_PACED = "self_paced"
    INSTRUCTOR_LED = "instructor_led"
    BLENDED = "blended"


class MembershipState(str, Enum):
    ACTIVE = "active"
    WAITLISTED = "waitlisted"
    REMOVED = "removed"


class SessionModality(str, Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


@dataclass
class Cohort:
    cohort_id: str
    tenant_id: str
    program_id: str
    cohort_name: str
    description: str
    start_date: datetime
    end_date: datetime
    capacity: int
    delivery_mode: DeliveryMode
    timezone: str
    facilitator_ids: List[str]
    enrollment_rules: Optional[Dict] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    status: CohortStatus = CohortStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CohortMembership:
    cohort_membership_id: str
    cohort_id: str
    tenant_id: str
    learner_id: str
    state: MembershipState
    assigned_by: str
    effective_date: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CohortSession:
    session_id: str
    title: str
    start_at: datetime
    end_at: datetime
    instructor_id: str
    modality: SessionModality


@dataclass
class CohortMilestoneDates:
    enrollment_cutoff: Optional[datetime] = None
    assignment_due_dates: Dict[str, datetime] = field(default_factory=dict)
    assessments: Dict[str, datetime] = field(default_factory=dict)


@dataclass
class CohortSchedule:
    cohort_id: str
    tenant_id: str
    session_plan: List[CohortSession] = field(default_factory=list)
    milestone_dates: CohortMilestoneDates = field(default_factory=CohortMilestoneDates)
    recurrence_rules: Optional[Dict] = None
    holiday_blackouts: List[str] = field(default_factory=list)
    schedule_version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEvent:
    event_type: str
    entity_id: str
    tenant_id: str
    payload: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)
