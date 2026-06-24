"""Media service — pipeline + playback security (B15-011 to B15-025)."""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from .security import (
    authorize_playback, _session_ctrl, _anti_piracy,
    WatermarkHooks, AntiPiracyHooks, _validate_playback_token,
)

app = FastAPI(title="Media Service", version="1.0.0")


@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


from .consumers import register_consumers as _register_consumers
_register_consumers()


class PlaybackAuthRequest(BaseModel):
    content_id: str
    device_id: str = "default"


class SessionRevokeRequest(BaseModel):
    session_id: str
    reason: str = "manual"


class WatermarkSignalRequest(BaseModel):
    user_id: str
    tenant_id: str
    content_id: str
    signal_type: str = "leak_detected"


@app.post("/api/v1/media/playback/authorize")
async def authorize(request: PlaybackAuthRequest,
                    x_user_id: str = Header(alias="X-User-Id", default=""),
                    x_tenant_id: str = Header(alias="X-Tenant-Id", default="")):
    """B15-011: entitlement-gated playback authorization."""
    status, body = authorize_playback(x_user_id, x_tenant_id,
                                       request.content_id, request.device_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=body)
    return body


@app.post("/api/v1/media/sessions/{session_id}/revoke")
async def revoke_session(session_id: str, request: SessionRevokeRequest,
                          x_user_id: str = Header(alias="X-User-Id", default=""),
                          x_tenant_id: str = Header(alias="X-Tenant-Id", default="")):
    """B15-024: revoke a media session on entitlement change or security trigger."""
    status, body = _session_ctrl.revoke_session(x_user_id, x_tenant_id, session_id, request.reason)
    if status != 200:
        raise HTTPException(status_code=status, detail=body)
    return body


@app.get("/api/v1/media/sessions")
async def list_sessions(x_user_id: str = Header(alias="X-User-Id", default=""),
                         x_tenant_id: str = Header(alias="X-Tenant-Id", default="")):
    """B15-024: list active sessions for user."""
    return {"sessions": _session_ctrl.list_sessions(x_user_id, x_tenant_id)}


@app.post("/api/v1/media/anti-piracy/watermark-signal")
async def watermark_signal(request: WatermarkSignalRequest):
    """B15-013: receive watermark signal from piracy detection — emit event."""
    WatermarkHooks.on_watermark_signal(request.model_dump())
    return {"status": "signal_received", "event_emitted": True}


@app.get("/api/v1/media/anti-piracy/anomaly-check")
async def anomaly_check(x_user_id: str = Header(alias="X-User-Id", default=""),
                         x_tenant_id: str = Header(alias="X-Tenant-Id", default="")):
    """B15-025: check for anomalous access patterns."""
    return _anti_piracy.detect_anomaly(x_user_id, x_tenant_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "media-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "media-service", "service_up": 1}

