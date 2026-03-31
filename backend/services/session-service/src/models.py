from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SessionStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELED = "canceled"
    ARCHIVED = "archived"


class DeliveryMode(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    HYBRID = "hybrid"


@dataclass
class SessionSchedule:
    timezone: str
    start_at: datetime
    end_at: datetime
    recurrence_rule: Optional[str] = None


@dataclass
class RescheduleRecord:
    previous_start_at: datetime
    previous_end_at: datetime
    new_start_at: datetime
    new_end_at: datetime
    actor_id: str
    reason: str
    changed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeliveryMetadata:
    join_instructions: Optional[str] = None
    recording_policy: str = "optional"
    location: Dict[str, str] = field(default_factory=dict)
    online_provider: Optional[str] = None
    online_join_url: Optional[str] = None
    online_host_url: Optional[str] = None
    dial_in_info: Optional[str] = None
    hybrid_attendance_policy: Optional[str] = None


@dataclass
class Session:
    session_id: str
    tenant_id: str
    status: SessionStatus
    title: str
    description: Optional[str]
    course_id: str
    lesson_id: Optional[str]
    cohort_ids: List[str]
    delivery_mode: DeliveryMode
    instructor_refs: List[str]
    capacity: Optional[int]
    waitlist_enabled: bool
    delivery_metadata: DeliveryMetadata
    schedule: Optional[SessionSchedule] = None
    reschedule_history: List[RescheduleRecord] = field(default_factory=list)
    created_by: str = "system"
    updated_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    version: int = 1


@dataclass
class AuditLog:
    audit_id: str
    tenant_id: str
    session_id: str
    action: str
    actor_id: str
    details: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EventMessage:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: Dict
    metadata: Dict = field(default_factory=dict)
