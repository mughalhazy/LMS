"""Service entrypoint."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Header, Query, status
from fastapi.responses import Response
from pydantic import BaseModel

from .security import apply_security_headers, require_jwt
from .service import SubscriptionNotFoundError, WebhookManagementService

app = FastAPI(title="webhook-service", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


apply_security_headers(app)

_SVC = WebhookManagementService()


# ── Request schemas ───────────────────────────────────────────────────────────

class CreateSubscriptionRequest(BaseModel):
    endpoint_url: str
    secret: str
    subscribed_events: list[str]
    subscription_id: str | None = None


class UpdateSubscriptionRequest(BaseModel):
    endpoint_url: str | None = None
    subscribed_events: list[str] | None = None


class PublishEventRequest(BaseModel):
    event_type: str
    data: dict[str, Any]
    event_id: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "webhook-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "webhook-service", "service_up": 1}


# B05-004: webhook-system-spec.md — subscription lifecycle routes

@app.post("/api/v1/webhooks/subscriptions", status_code=status.HTTP_201_CREATED)
def create_subscription(
    request: CreateSubscriptionRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SVC.create_subscription(
        tenant_id=x_tenant_id,
        endpoint_url=request.endpoint_url,
        secret=request.secret,
        subscribed_events=request.subscribed_events,
        subscription_id=request.subscription_id,
    )


@app.get("/api/v1/webhooks/subscriptions")
def list_subscriptions(
    x_tenant_id: str | None = Header(default=None),
    sub_status: str | None = Query(default=None, alias="status"),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    items = _SVC.list_subscriptions(tenant_id=x_tenant_id, status=sub_status)
    return {"subscriptions": items, "total": len(items)}


@app.get("/api/v1/webhooks/subscriptions/{subscription_id}")
def get_subscription(
    subscription_id: str,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SVC.get_subscription(tenant_id=x_tenant_id, subscription_id=subscription_id)
    except (SubscriptionNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/api/v1/webhooks/subscriptions/{subscription_id}")
def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SVC.update_subscription(
            tenant_id=x_tenant_id,
            subscription_id=subscription_id,
            endpoint_url=request.endpoint_url,
            subscribed_events=request.subscribed_events,
        )
    except (SubscriptionNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/v1/webhooks/subscriptions/{subscription_id}", status_code=status.HTTP_200_OK)
def delete_subscription(
    subscription_id: str,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SVC.delete_subscription(tenant_id=x_tenant_id, subscription_id=subscription_id)
    except (SubscriptionNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/webhooks/events", status_code=status.HTTP_202_ACCEPTED)
def publish_event(
    request: PublishEventRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SVC.publish_event(
        tenant_id=x_tenant_id,
        event_type=request.event_type,
        data=request.data,
        event_id=request.event_id,
    )


@app.post("/api/v1/webhooks/deliveries/process")
def process_deliveries(x_tenant_id: str | None = Header(default=None)) -> dict:
    """Run the delivery engine with a simulated transport (best-effort HTTP simulation)."""
    def _simulated_transport(url: str, payload: str, headers: dict, timeout: int):
        return (200, "ok") if "invalid" not in url else (500, "error")
    return _SVC.process_due_deliveries(transport=_simulated_transport)


@app.get("/api/v1/webhooks/deliveries/dead-letter")
def get_dead_letter_queue(
    x_tenant_id: str | None = Header(default=None),
    event_type: str | None = Query(default=None),
) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    items = _SVC.get_dead_letter_queue(tenant_id=x_tenant_id, event_type=event_type)
    return {"dead_letters": items, "total": len(items)}


@app.get("/api/v1/webhooks/deliveries/pending")
def get_pending_deliveries(x_tenant_id: str | None = Header(default=None)) -> dict:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    items = _SVC.get_pending_deliveries(tenant_id=x_tenant_id)
    return {"pending": items, "total": len(items)}

