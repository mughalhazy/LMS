from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TicketStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    WAITING_ON_EMPLOYEE = "waiting_on_employee"
    RESOLVED = "resolved"
    CLOSED = "closed"


class HelpdeskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class HelpdeskCategory(str, Enum):
    PAYROLL = "payroll"
    BENEFITS = "benefits"
    LEAVE = "leave"
    ONBOARDING = "onboarding"
    COMPLIANCE = "compliance"
    POLICY = "policy"
    GENERAL = "general"


class AutomationTrigger(str, Enum):
    TICKET_CREATED = "ticket_created"
    PRIORITY_CHANGED = "priority_changed"
    SLA_AT_RISK = "sla_at_risk"
    STATUS_CHANGED = "status_changed"


@dataclass
class TicketComment:
    author_id: str
    body: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class AutomationHook:
    tenant_id: str
    name: str
    callback_target: str
    trigger: AutomationTrigger
    min_priority: HelpdeskPriority | None = None
    category: HelpdeskCategory | None = None
    statuses: set[TicketStatus] = field(default_factory=set)
    enabled: bool = True
    hook_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class AutomationDispatch:
    tenant_id: str
    hook_id: str
    ticket_id: str
    trigger: AutomationTrigger
    callback_target: str
    payload: dict[str, Any]
    delivered: bool
    dispatch_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class HelpdeskTicket:
    tenant_id: str
    employee_id: str
    subject: str
    description: str
    category: HelpdeskCategory
    urgency_level: int
    impacted_employee_count: int
    requested_by_manager: bool
    due_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    ticket_id: str = field(default_factory=lambda: str(uuid4()))
    status: TicketStatus = TicketStatus.OPEN
    priority: HelpdeskPriority = HelpdeskPriority.MEDIUM
    priority_score: float = 0.0
    priority_factors: dict[str, float] = field(default_factory=dict)
    assigned_to: str | None = None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_summary: str | None = None
    reopened_count: int = 0
    comments: list[TicketComment] = field(default_factory=list)
    automation_dispatches: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
