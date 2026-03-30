from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import AutomationTrigger, HelpdeskCategory, HelpdeskPriority, TicketStatus


class CreateTicketRequest(BaseModel):
    tenant_id: str
    employee_id: str
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category: HelpdeskCategory
    urgency_level: int = Field(ge=1, le=5)
    impacted_employee_count: int = Field(default=1, ge=1)
    requested_by_manager: bool = False
    due_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class TicketCommentRequest(BaseModel):
    tenant_id: str
    author_id: str
    body: str = Field(min_length=1)


class UpdateTicketRequest(BaseModel):
    tenant_id: str
    updated_by: str
    status: TicketStatus | None = None
    assigned_to: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    impacted_employee_count: int | None = Field(default=None, ge=1)
    requested_by_manager: bool | None = None
    due_at: datetime | None = None
    resolution_summary: str | None = None
    tags: list[str] | None = None


class TicketResponse(BaseModel):
    ticket_id: str
    tenant_id: str
    employee_id: str
    subject: str
    description: str
    category: HelpdeskCategory
    status: TicketStatus
    priority: HelpdeskPriority
    priority_score: float
    priority_factors: dict[str, float]
    urgency_level: int
    impacted_employee_count: int
    requested_by_manager: bool
    assigned_to: str | None = None
    due_at: datetime | None = None
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_summary: str | None = None
    reopened_count: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int


class QueueTicketResponse(BaseModel):
    ticket_id: str
    subject: str
    category: HelpdeskCategory
    status: TicketStatus
    priority: HelpdeskPriority
    priority_score: float
    priority_factors: dict[str, float]
    assigned_to: str | None = None
    due_at: datetime | None = None
    created_at: datetime


class QueueResponse(BaseModel):
    items: list[QueueTicketResponse]
    total: int


class RegisterAutomationHookRequest(BaseModel):
    tenant_id: str
    name: str
    callback_target: str
    trigger: AutomationTrigger
    min_priority: HelpdeskPriority | None = None
    category: HelpdeskCategory | None = None
    statuses: list[TicketStatus] = Field(default_factory=list)
    enabled: bool = True


class AutomationHookResponse(BaseModel):
    hook_id: str
    tenant_id: str
    name: str
    callback_target: str
    trigger: AutomationTrigger
    min_priority: HelpdeskPriority | None = None
    category: HelpdeskCategory | None = None
    statuses: list[TicketStatus]
    enabled: bool
    created_at: datetime


class AutomationDispatchResponse(BaseModel):
    dispatch_id: str
    hook_id: str
    ticket_id: str
    trigger: AutomationTrigger
    callback_target: str
    delivered: bool
    payload: dict[str, Any]
    created_at: datetime


class AutomationDispatchListResponse(BaseModel):
    items: list[AutomationDispatchResponse]
    total: int


class AnalyticsResponse(BaseModel):
    tenant_id: str
    generated_at: datetime
    totals: dict[str, int]
    status_breakdown: dict[str, int]
    priority_breakdown: dict[str, int]
    category_breakdown: dict[str, int]
    assignment_breakdown: dict[str, int]
    sla: dict[str, float | int]
    automation: dict[str, float | int]
    queue_insights: dict[str, Any]
