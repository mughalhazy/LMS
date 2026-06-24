"""Service entrypoint — integration-service HTTP API.

B12-001: integration-service-spec.md defines 4 capabilities + integration-api.md defines
4 routes; service.py (PlatformIntegrationService) implements the 6-step decision
orchestrator; openapi.yaml exists — but no main.py existed to serve the API.
"""
from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.responses import Response

from .consumers import register_consumers as _register_consumers
from .service import PlatformIntegrationService

_register_consumers()

_SVC = PlatformIntegrationService()

# ── JWT auth ──────────────────────────────────────────────────────────────────

_AUTH_SCHEME = HTTPBearer(auto_error=False)
_EXEMPT_PATHS = {"/health", "/metrics", "/openapi.json", "/docs", "/redoc"}


def _decode_b64url(v: str) -> bytes:
    return base64.urlsafe_b64decode(v + "=" * ((4 - len(v) % 4) % 4))


def require_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_AUTH_SCHEME),
) -> None:
    if request.url.path in _EXEMPT_PATHS:
        return
    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="jwt_secret_not_configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    tok = credentials.credentials
    try:
        h, p, s = tok.split(".")
        expected = _hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not _hmac.compare_digest(expected, _decode_b64url(s)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")
        payload = json.loads(_decode_b64url(p))
        exp = payload.get("exp")
        if exp is not None and float(exp) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
        request.state.jwt_payload = payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="integration-service", version="1.0.0", dependencies=[Depends(require_jwt)])


@app.middleware("http")
async def _add_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# ── Request schemas ───────────────────────────────────────────────────────────

class CapabilityEvalRequest(BaseModel):
    tenant_id: str
    actor_id: str
    capability_key: str
    resource_context: dict[str, Any] | None = None
    request_context: dict[str, Any] | None = None


class HrisSyncRequest(BaseModel):
    tenant_id: str
    actor_id: str
    employee_records: list[dict[str, Any]]
    sync_mode: str = "delta"


class CrmUpsertRequest(BaseModel):
    tenant_id: str
    actor_id: str
    contacts: list[dict[str, Any]]


class LtiLaunchRequest(BaseModel):
    tenant_id: str
    tool_id: str
    user_id: str
    course_id: str | None = None


class WebhookEventRequest(BaseModel):
    tenant_id: str
    event_type: str
    data: dict[str, Any]
    signature: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "integration-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "integration-service", "service_up": 1}


@app.post("/api/v1/integration/evaluate")
def evaluate_capability(req: CapabilityEvalRequest) -> dict:
    """Core decision endpoint — 6-step capability evaluation per B2P08."""
    return _SVC.evaluate_capability(
        tenant_id=req.tenant_id,
        actor_id=req.actor_id,
        capability_key=req.capability_key,
        resource_context=req.resource_context,
        request_context=req.request_context,
    )


# B12-001: integration-api.md — 4 integration routing endpoints

@app.post("/api/integrations/hris/employees/sync", status_code=status.HTTP_202_ACCEPTED)
def hris_sync(
    req: HrisSyncRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    """Route HRIS employee sync through capability gate, then delegate to hris-sync-service."""
    tid = req.tenant_id or x_tenant_id
    if not tid:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    decision = _SVC.evaluate_capability(tenant_id=tid, actor_id=req.actor_id,
                                         capability_key="cap.hris.sync")
    if decision["decision"] == "DENY":
        raise HTTPException(status_code=403, detail=decision["reason_codes"])
    return {"status": "accepted", "tenant_id": tid, "records": len(req.employee_records),
            "evaluation_trace_id": decision["evaluation_trace_id"]}


@app.post("/api/integrations/crm/contacts/upsert", status_code=status.HTTP_202_ACCEPTED)
def crm_upsert(
    req: CrmUpsertRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    """Route CRM contact upsert through capability gate."""
    tid = req.tenant_id or x_tenant_id
    if not tid:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    decision = _SVC.evaluate_capability(tenant_id=tid, actor_id=req.actor_id,
                                         capability_key="cap.crm.upsert")
    if decision["decision"] == "DENY":
        raise HTTPException(status_code=403, detail=decision["reason_codes"])
    return {"status": "accepted", "tenant_id": tid, "contacts": len(req.contacts),
            "evaluation_trace_id": decision["evaluation_trace_id"]}


@app.post("/api/integrations/lti/launch", status_code=status.HTTP_200_OK)
def lti_launch(
    req: LtiLaunchRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    """Route LTI launch through capability gate, then delegate to lti-service."""
    tid = req.tenant_id or x_tenant_id
    if not tid:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    decision = _SVC.evaluate_capability(tenant_id=tid, actor_id=req.user_id,
                                         capability_key="cap.lti.launch")
    if decision["decision"] == "DENY":
        raise HTTPException(status_code=403, detail=decision["reason_codes"])
    return {"status": "launch_authorized", "tenant_id": tid, "tool_id": req.tool_id,
            "evaluation_trace_id": decision["evaluation_trace_id"]}


@app.post("/api/integrations/webhooks/events", status_code=status.HTTP_202_ACCEPTED)
def webhook_event(
    req: WebhookEventRequest,
    x_tenant_id: str | None = Header(default=None),
) -> dict:
    """Route inbound webhook event through capability gate, then dispatch."""
    tid = req.tenant_id or x_tenant_id
    if not tid:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    decision = _SVC.evaluate_capability(tenant_id=tid, actor_id="system",
                                         capability_key="cap.webhook.ingest")
    if decision["decision"] == "DENY":
        raise HTTPException(status_code=403, detail=decision["reason_codes"])
    return {"status": "accepted", "tenant_id": tid, "event_type": req.event_type,
            "evaluation_trace_id": decision["evaluation_trace_id"]}
