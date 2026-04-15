from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import HTTPException

from .models import (
    AutomationDispatch,
    AutomationHook,
    AutomationTrigger,
    HelpdeskCategory,
    HelpdeskPriority,
    HelpdeskTicket,
    TicketComment,
    TicketStatus,
)
from .schemas import (
    AnalyticsResponse,
    AutomationDispatchListResponse,
    AutomationDispatchResponse,
    AutomationHookResponse,
    CreateTicketRequest,
    QueueResponse,
    QueueTicketResponse,
    RegisterAutomationHookRequest,
    TicketCommentRequest,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
)
from .store import HelpdeskStore


CATEGORY_WEIGHTS: dict[HelpdeskCategory, float] = {
    HelpdeskCategory.PAYROLL: 24.0,
    HelpdeskCategory.BENEFITS: 18.0,
    HelpdeskCategory.LEAVE: 16.0,
    HelpdeskCategory.ONBOARDING: 14.0,
    HelpdeskCategory.COMPLIANCE: 22.0,
    HelpdeskCategory.POLICY: 10.0,
    HelpdeskCategory.GENERAL: 8.0,
}

PRIORITY_RANK = {
    HelpdeskPriority.LOW: 1,
    HelpdeskPriority.MEDIUM: 2,
    HelpdeskPriority.HIGH: 3,
    HelpdeskPriority.URGENT: 4,
}


class HRHelpdeskService:
    def __init__(self, store: HelpdeskStore) -> None:
        self.store = store

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        ticket = HelpdeskTicket(
            tenant_id=request.tenant_id,
            employee_id=request.employee_id,
            subject=request.subject,
            description=request.description,
            category=request.category,
            urgency_level=request.urgency_level,
            impacted_employee_count=request.impacted_employee_count,
            requested_by_manager=request.requested_by_manager,
            due_at=request.due_at,
            tags=sorted(set(request.tags)),
        )
        self._recompute_priority(ticket)
        self.store.save_ticket(ticket)
        self._dispatch_automation(ticket=ticket, trigger=AutomationTrigger.TICKET_CREATED)
        if self._is_sla_at_risk(ticket):
            self._dispatch_automation(ticket=ticket, trigger=AutomationTrigger.SLA_AT_RISK)
        return self._ticket_response(ticket)

    def update_ticket(self, ticket_id: str, request: UpdateTicketRequest) -> TicketResponse:
        ticket = self._get_ticket_for_tenant(request.tenant_id, ticket_id)
        previous_priority = ticket.priority
        previous_priority_score = ticket.priority_score
        previous_status = ticket.status
        now = self._now()

        if request.assigned_to is not None:
            ticket.assigned_to = request.assigned_to
            if request.assigned_to and ticket.first_response_at is None:
                ticket.first_response_at = now

        if request.status is not None:
            if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED} and request.status == TicketStatus.IN_PROGRESS:
                ticket.reopened_count += 1
            ticket.status = request.status
            if request.status == TicketStatus.RESOLVED:
                ticket.resolved_at = now
            if request.status == TicketStatus.CLOSED and ticket.resolved_at is None:
                ticket.resolved_at = now

        if request.urgency_level is not None:
            ticket.urgency_level = request.urgency_level
        if request.impacted_employee_count is not None:
            ticket.impacted_employee_count = request.impacted_employee_count
        if request.requested_by_manager is not None:
            ticket.requested_by_manager = request.requested_by_manager
        if request.tags is not None:
            ticket.tags = sorted(set(request.tags))
        if request.resolution_summary is not None:
            ticket.resolution_summary = request.resolution_summary
        ticket.due_at = request.due_at if request.due_at is not None else ticket.due_at

        self._recompute_priority(ticket)
        ticket.updated_at = now
        self.store.save_ticket(ticket)

        if ticket.priority != previous_priority or ticket.priority_score != previous_priority_score:
            self._dispatch_automation(ticket=ticket, trigger=AutomationTrigger.PRIORITY_CHANGED)
        if ticket.status != previous_status:
            self._dispatch_automation(ticket=ticket, trigger=AutomationTrigger.STATUS_CHANGED)
        if self._is_sla_at_risk(ticket):
            self._dispatch_automation(ticket=ticket, trigger=AutomationTrigger.SLA_AT_RISK)

        return self._ticket_response(ticket)

    def add_comment(self, ticket_id: str, request: TicketCommentRequest) -> TicketResponse:
        ticket = self._get_ticket_for_tenant(request.tenant_id, ticket_id)
        ticket.comments.append(TicketComment(author_id=request.author_id, body=request.body))
        ticket.updated_at = self._now()
        self.store.save_ticket(ticket)
        return self._ticket_response(ticket)

    def list_tickets(self, tenant_id: str, status: TicketStatus | None = None, assigned_to: str | None = None) -> TicketListResponse:
        tickets = self.store.list_tickets(tenant_id)
        if status is not None:
            tickets = [ticket for ticket in tickets if ticket.status == status]
        if assigned_to is not None:
            tickets = [ticket for ticket in tickets if ticket.assigned_to == assigned_to]
        ordered = sorted(tickets, key=lambda ticket: (ticket.created_at, ticket.ticket_id), reverse=True)
        return TicketListResponse(items=[self._ticket_response(ticket) for ticket in ordered], total=len(ordered))

    def get_prioritized_queue(self, tenant_id: str, assigned_to: str | None = None) -> QueueResponse:
        tickets = [
            ticket
            for ticket in self.store.list_tickets(tenant_id)
            if ticket.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
            and (assigned_to is None or ticket.assigned_to == assigned_to)
        ]
        ordered = sorted(
            tickets,
            key=lambda ticket: (
                ticket.priority_score,
                1 if self._is_sla_at_risk(ticket) else 0,
                -ticket.created_at.timestamp(),
            ),
            reverse=True,
        )
        return QueueResponse(
            items=[
                QueueTicketResponse(
                    ticket_id=ticket.ticket_id,
                    subject=ticket.subject,
                    category=ticket.category,
                    status=ticket.status,
                    priority=ticket.priority,
                    priority_score=ticket.priority_score,
                    priority_factors=ticket.priority_factors,
                    assigned_to=ticket.assigned_to,
                    due_at=ticket.due_at,
                    created_at=ticket.created_at,
                )
                for ticket in ordered
            ],
            total=len(ordered),
        )

    def register_automation_hook(self, request: RegisterAutomationHookRequest) -> AutomationHookResponse:
        hook = AutomationHook(
            tenant_id=request.tenant_id,
            name=request.name,
            callback_target=request.callback_target,
            trigger=request.trigger,
            min_priority=request.min_priority,
            category=request.category,
            statuses=set(request.statuses),
            enabled=request.enabled,
        )
        self.store.save_hook(hook)
        return self._hook_response(hook)

    def list_dispatches(self, tenant_id: str, ticket_id: str | None = None) -> AutomationDispatchListResponse:
        dispatches = self.store.list_dispatches(tenant_id)
        if ticket_id is not None:
            dispatches = [dispatch for dispatch in dispatches if dispatch.ticket_id == ticket_id]
        ordered = sorted(dispatches, key=lambda item: item.created_at, reverse=True)
        return AutomationDispatchListResponse(
            items=[self._dispatch_response(dispatch) for dispatch in ordered],
            total=len(ordered),
        )

    def analytics_snapshot(self, tenant_id: str) -> AnalyticsResponse:
        tickets = self.store.list_tickets(tenant_id)
        now = self._now()
        status_breakdown = Counter(ticket.status.value for ticket in tickets)
        priority_breakdown = Counter(ticket.priority.value for ticket in tickets)
        category_breakdown = Counter(ticket.category.value for ticket in tickets)
        assignment_breakdown = Counter(ticket.assigned_to or "unassigned" for ticket in tickets)
        dispatches = self.store.list_dispatches(tenant_id)

        open_tickets = [ticket for ticket in tickets if ticket.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}]
        sla_at_risk = [ticket for ticket in open_tickets if self._is_sla_at_risk(ticket)]
        response_minutes = [
            max((ticket.first_response_at - ticket.created_at).total_seconds() / 60, 0.0)
            for ticket in tickets
            if ticket.first_response_at is not None
        ]
        resolution_hours = [
            max((ticket.resolved_at - ticket.created_at).total_seconds() / 3600, 0.0)
            for ticket in tickets
            if ticket.resolved_at is not None
        ]

        queue = self.get_prioritized_queue(tenant_id)
        delivered = sum(1 for dispatch in dispatches if dispatch.delivered)
        totals = {
            "tickets": len(tickets),
            "open_tickets": len(open_tickets),
            "resolved_tickets": len([ticket for ticket in tickets if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}]),
            "unassigned_tickets": assignment_breakdown.get("unassigned", 0),
        }

        return AnalyticsResponse(
            tenant_id=tenant_id,
            generated_at=now,
            totals=totals,
            status_breakdown=dict(status_breakdown),
            priority_breakdown=dict(priority_breakdown),
            category_breakdown=dict(category_breakdown),
            assignment_breakdown=dict(assignment_breakdown),
            sla={
                "at_risk_count": len(sla_at_risk),
                "at_risk_rate": round((len(sla_at_risk) / len(open_tickets) * 100), 2) if open_tickets else 0.0,
                "avg_first_response_minutes": round(sum(response_minutes) / len(response_minutes), 2) if response_minutes else 0.0,
                "avg_resolution_hours": round(sum(resolution_hours) / len(resolution_hours), 2) if resolution_hours else 0.0,
            },
            automation={
                "configured_hooks": len(self.store.list_hooks(tenant_id)),
                "dispatches": len(dispatches),
                "successful_dispatches": delivered,
                "success_rate": round((delivered / len(dispatches) * 100), 2) if dispatches else 0.0,
            },
            queue_insights={
                "highest_priority_ticket_id": queue.items[0].ticket_id if queue.items else None,
                "top_priority_score": queue.items[0].priority_score if queue.items else 0.0,
                "top_categories": category_breakdown.most_common(3),
            },
        )

    def _dispatch_automation(self, *, ticket: HelpdeskTicket, trigger: AutomationTrigger) -> None:
        for hook in self.store.list_hooks(ticket.tenant_id):
            if not hook.enabled or hook.trigger != trigger:
                continue
            if hook.min_priority and PRIORITY_RANK[ticket.priority] < PRIORITY_RANK[hook.min_priority]:
                continue
            if hook.category and hook.category != ticket.category:
                continue
            if hook.statuses and ticket.status not in hook.statuses:
                continue

            dispatch = AutomationDispatch(
                tenant_id=ticket.tenant_id,
                hook_id=hook.hook_id,
                ticket_id=ticket.ticket_id,
                trigger=trigger,
                callback_target=hook.callback_target,
                payload={
                    "ticket_id": ticket.ticket_id,
                    "tenant_id": ticket.tenant_id,
                    "priority": ticket.priority.value,
                    "priority_score": ticket.priority_score,
                    "status": ticket.status.value,
                    "category": ticket.category.value,
                },
                delivered=True,
            )
            self.store.save_dispatch(dispatch)
            ticket.automation_dispatches.append(dispatch.dispatch_id)

    def _recompute_priority(self, ticket: HelpdeskTicket) -> None:
        now = self._now()
        due_in_hours = 9999.0
        if ticket.due_at is not None:
            due_in_hours = (ticket.due_at - now).total_seconds() / 3600

        factors = {
            "category": CATEGORY_WEIGHTS[ticket.category],
            "urgency": float(ticket.urgency_level * 9),
            "impact": float(min(ticket.impacted_employee_count, 25) * 1.8),
            "manager_escalation": 8.0 if ticket.requested_by_manager else 0.0,
            "reopen_penalty": float(ticket.reopened_count * 6),
            "sla_risk": 18.0 if due_in_hours <= 8 else (10.0 if due_in_hours <= 24 else 0.0),
        }
        ticket.priority_factors = factors
        ticket.priority_score = round(sum(factors.values()), 2)
        if ticket.priority_score >= 80:
            ticket.priority = HelpdeskPriority.URGENT
        elif ticket.priority_score >= 55:
            ticket.priority = HelpdeskPriority.HIGH
        elif ticket.priority_score >= 30:
            ticket.priority = HelpdeskPriority.MEDIUM
        else:
            ticket.priority = HelpdeskPriority.LOW

    def _is_sla_at_risk(self, ticket: HelpdeskTicket) -> bool:
        if ticket.due_at is None or ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
            return False
        hours_remaining = (ticket.due_at - self._now()).total_seconds() / 3600
        return hours_remaining <= 8

    def _get_ticket_for_tenant(self, tenant_id: str, ticket_id: str) -> HelpdeskTicket:
        ticket = self.store.get_ticket(ticket_id)
        if ticket is None or ticket.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="ticket_not_found")
        return ticket

    @staticmethod
    def _ticket_response(ticket: HelpdeskTicket) -> TicketResponse:
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            tenant_id=ticket.tenant_id,
            employee_id=ticket.employee_id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            priority_score=ticket.priority_score,
            priority_factors=ticket.priority_factors,
            urgency_level=ticket.urgency_level,
            impacted_employee_count=ticket.impacted_employee_count,
            requested_by_manager=ticket.requested_by_manager,
            assigned_to=ticket.assigned_to,
            due_at=ticket.due_at,
            first_response_at=ticket.first_response_at,
            resolved_at=ticket.resolved_at,
            resolution_summary=ticket.resolution_summary,
            reopened_count=ticket.reopened_count,
            tags=ticket.tags,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

    @staticmethod
    def _hook_response(hook: AutomationHook) -> AutomationHookResponse:
        return AutomationHookResponse(
            hook_id=hook.hook_id,
            tenant_id=hook.tenant_id,
            name=hook.name,
            callback_target=hook.callback_target,
            trigger=hook.trigger,
            min_priority=hook.min_priority,
            category=hook.category,
            statuses=sorted(hook.statuses, key=lambda status: status.value),
            enabled=hook.enabled,
            created_at=hook.created_at,
        )

    @staticmethod
    def _dispatch_response(dispatch: AutomationDispatch) -> AutomationDispatchResponse:
        return AutomationDispatchResponse(
            dispatch_id=dispatch.dispatch_id,
            hook_id=dispatch.hook_id,
            ticket_id=dispatch.ticket_id,
            trigger=dispatch.trigger,
            callback_target=dispatch.callback_target,
            delivered=dispatch.delivered,
            payload=dispatch.payload,
            created_at=dispatch.created_at,
        )
