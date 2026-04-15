from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException

from .models import TicketStatus
from .schemas import (
    AnalyticsResponse,
    AutomationDispatchListResponse,
    AutomationHookResponse,
    CreateTicketRequest,
    QueueResponse,
    RegisterAutomationHookRequest,
    TicketCommentRequest,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
)
from .service import HRHelpdeskService
from .store import InMemoryHelpdeskStore

app = FastAPI(title="HR Helpdesk Service", version="0.1.0")
service = HRHelpdeskService(store=InMemoryHelpdeskStore())


def tenant_context(x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="tenant_context_missing")
    return x_tenant_id


@app.post("/api/v1/hr-helpdesk/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(request: CreateTicketRequest, tenant_id: str = Depends(tenant_context)) -> TicketResponse:
    if request.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.create_ticket(request)


@app.patch("/api/v1/hr-helpdesk/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: str, request: UpdateTicketRequest, tenant_id: str = Depends(tenant_context)) -> TicketResponse:
    if request.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.update_ticket(ticket_id, request)


@app.post("/api/v1/hr-helpdesk/tickets/{ticket_id}/comments", response_model=TicketResponse)
def add_ticket_comment(
    ticket_id: str,
    request: TicketCommentRequest,
    tenant_id: str = Depends(tenant_context),
) -> TicketResponse:
    if request.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.add_comment(ticket_id, request)


@app.get("/api/v1/hr-helpdesk/tickets", response_model=TicketListResponse)
def list_tickets(
    status: TicketStatus | None = None,
    assigned_to: str | None = None,
    tenant_id: str = Depends(tenant_context),
) -> TicketListResponse:
    return service.list_tickets(tenant_id=tenant_id, status=status, assigned_to=assigned_to)


@app.get("/api/v1/hr-helpdesk/queue", response_model=QueueResponse)
def prioritized_queue(assigned_to: str | None = None, tenant_id: str = Depends(tenant_context)) -> QueueResponse:
    return service.get_prioritized_queue(tenant_id=tenant_id, assigned_to=assigned_to)


@app.post("/api/v1/hr-helpdesk/automation/hooks", response_model=AutomationHookResponse, status_code=201)
def register_automation_hook(
    request: RegisterAutomationHookRequest,
    tenant_id: str = Depends(tenant_context),
) -> AutomationHookResponse:
    if request.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.register_automation_hook(request)


@app.get("/api/v1/hr-helpdesk/automation/dispatches", response_model=AutomationDispatchListResponse)
def list_automation_dispatches(
    ticket_id: str | None = None,
    tenant_id: str = Depends(tenant_context),
) -> AutomationDispatchListResponse:
    return service.list_dispatches(tenant_id=tenant_id, ticket_id=ticket_id)


@app.get("/api/v1/hr-helpdesk/analytics", response_model=AnalyticsResponse)
def analytics_snapshot(tenant_id: str = Depends(tenant_context)) -> AnalyticsResponse:
    return service.analytics_snapshot(tenant_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hr-helpdesk-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    analytics = service.analytics_snapshot("__metrics__")
    return {
        "service": "hr-helpdesk-service",
        "service_up": 1,
        "tickets_total": analytics.totals["tickets"],
        "open_tickets": analytics.totals["open_tickets"],
        "automation_dispatches": int(analytics.automation["dispatches"]),
    }
