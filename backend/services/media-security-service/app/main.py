"""Media Security Service — standalone service implementing media-security-interface-contract.md.
B15-014: deployment boundary separation from media-service.
Handles CAP-SESSION-CONTROL and CAP-ANTI-PIRACY-ENFORCEMENT as a dedicated service."""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .service import MediaSecurityService

app = FastAPI(title="Media Security Service", version="1.0.0")
svc = MediaSecurityService()


@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


class AuthorizePlaybackRequest(BaseModel):
    content_id: str
    device_id: str = "default"
    expires_in: int = 3600


class RevokeSessionRequest(BaseModel):
    reason: str = "manual"


class WatermarkSignalRequest(BaseModel):
    signal_type: str
    content_id: str
    detected_at: str = ""


@app.post("/api/v1/media-security/playback/authorize")
async def authorize_playback(
    request: AuthorizePlaybackRequest,
    x_user_id: str = Header(alias="X-User-Id", default=""),
    x_tenant_id: str = Header(alias="X-Tenant-Id", default=""),
):
    """B15-011: authorizePlayback — full entitlement-gated flow."""
    status, body = svc.authorize_playback(x_user_id, x_tenant_id,
                                           request.content_id, request.device_id, request.expires_in)
    if status not in (200, 201):
        raise HTTPException(status_code=status, detail=body)
    return body


@app.post("/api/v1/media-security/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str, request: RevokeSessionRequest,
    x_user_id: str = Header(alias="X-User-Id", default=""),
    x_tenant_id: str = Header(alias="X-Tenant-Id", default=""),
):
    """B15-024: CAP-SESSION-CONTROL — revoke session on entitlement or security trigger."""
    status, body = svc.revoke_session(x_user_id, x_tenant_id, session_id, request.reason)
    if status != 200:
        raise HTTPException(status_code=status, detail=body)
    return body


@app.get("/api/v1/media-security/sessions")
async def list_sessions(
    x_user_id: str = Header(alias="X-User-Id", default=""),
    x_tenant_id: str = Header(alias="X-Tenant-Id", default=""),
):
    return {"sessions": svc.list_sessions(x_user_id, x_tenant_id)}


@app.post("/api/v1/media-security/anti-piracy/watermark-signal")
async def watermark_signal(request: WatermarkSignalRequest,
                            x_tenant_id: str = Header(alias="X-Tenant-Id", default=""),
                            x_user_id: str = Header(alias="X-User-Id", default="")):
    """B15-013: receive watermark signal, emit piracy event."""
    svc.handle_watermark_signal({**request.model_dump(),
                                  "user_id": x_user_id, "tenant_id": x_tenant_id})
    return {"status": "signal_received"}


@app.get("/api/v1/media-security/anti-piracy/anomaly-check")
async def anomaly_check(x_user_id: str = Header(alias="X-User-Id", default=""),
                         x_tenant_id: str = Header(alias="X-Tenant-Id", default="")):
    """B15-025: anomaly detection for unusual stream access patterns."""
    return svc.detect_anomaly(x_user_id, x_tenant_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "media-security-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "media-security-service", "service_up": 1}
