from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse

_NOTIF_EXEMPT = {"/health", "/metrics"}


def _jwt_valid(auth_header: str | None) -> bool:
    """B05-002: validate HS256 JWT from Authorization: Bearer header."""
    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        return True
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    try:
        h, p, s = token.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        expected = _hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        received = base64.urlsafe_b64decode(_pad(s))
        if not _hmac.compare_digest(expected, received):
            return False
        payload = json.loads(base64.urlsafe_b64decode(_pad(p)))
        exp = payload.get("exp")
        return exp is None or float(exp) >= time.time()
    except Exception:
        return False

from .schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from .service import NotificationService
from .store import InMemoryNotificationStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryNotificationStore()
SERVICE = NotificationService(STORE)

# OA-001: ASGI shim — same pattern as auth-service / checkout-service (Task 7)
app = FastAPI(title="Notification Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}


@app.get("/metrics")
async def metrics():
    return {"service": "notification-service", "service_up": 1}


@app.post("/api/v1/notifications/preferences")
async def upsert_preference(request: PreferenceUpsertRequest, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.upsert_preference(request)
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/notifications/preferences")
async def list_preferences(tenant_id: str = Query(...), user_id: str = Query(...), authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.list_preferences(tenant_id, user_id)
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/v1/notifications/routes")
async def upsert_event_route(request: EventRouteUpsertRequest, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.upsert_event_route(request)
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/v1/notifications/orchestrate")
async def orchestrate_notification(request: NotificationOrchestrationRequest, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.orchestrate_notification(request)
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/v1/notifications/events")
async def process_event(request: EventNotificationRequest, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.process_event(request)
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/v1/notifications/deliveries/drain")
async def drain_delivery_queue(request: DeliveryDrainRequest, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.drain_delivery_queue(request)
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/notifications/inbox")
async def list_inbox(tenant_id: str = Query(...), user_id: str = Query(...), status: Optional[str] = Query(None), limit: int = Query(50), authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    messages = STORE.list_messages(tenant_id=tenant_id, user_id=user_id, status=status, limit=limit)
    payload = {
        "messages": [
            {
                "message_id": m.message_id,
                "tenant_id": m.tenant_id,
                "user_id": m.user_id,
                "category": m.category,
                "channel": m.channel,
                "subject": m.subject,
                "body": m.body,
                "event_id": m.event_id,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
                "delivered_at": m.delivered_at.isoformat() if m.delivered_at else None,
            }
            for m in messages
        ],
        "total": len(messages),
    }
    return JSONResponse(status_code=200, content=payload)


class NotificationRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in _NOTIF_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            return self._send(401, {"error": "unauthorized"})
        try:
            body = self._read_json()
            if self.path == "/api/v1/notifications/preferences":
                status, payload = SERVICE.upsert_preference(PreferenceUpsertRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/routes":
                status, payload = SERVICE.upsert_event_route(EventRouteUpsertRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/orchestrate":
                status, payload = SERVICE.orchestrate_notification(NotificationOrchestrationRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/events":
                status, payload = SERVICE.process_event(EventNotificationRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/deliveries/drain":
                status, payload = SERVICE.drain_delivery_queue(DeliveryDrainRequest(**body))
                return self._send(status, payload)

            self._send(404, {"error": "not_found"})
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except KeyError as exc:
            self._send(400, {"error": "template_render_error", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in _NOTIF_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            return self._send(401, {"error": "unauthorized"})
        if self.path == "/health":
            return self._send(200, {"status": "ok", "service": "notification-service"})
        if self.path == "/metrics":
            return self._send(200, {"service": "notification-service", "service_up": 1})

        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/api/v1/notifications/preferences":
            tenant_id = query.get("tenant_id", [""])[0]
            user_id = query.get("user_id", [""])[0]
            if not tenant_id or not user_id:
                return self._send(400, {"error": "tenant_id_and_user_id_required"})
            status, payload = SERVICE.list_preferences(tenant_id, user_id)
            return self._send(status, payload)

        # Spec: notification-service — inbox read path for in_app channel messages
        if parsed.path == "/api/v1/notifications/inbox":
            tenant_id = query.get("tenant_id", [""])[0]
            user_id = query.get("user_id", [""])[0]
            if not tenant_id or not user_id:
                return self._send(400, {"error": "tenant_id_and_user_id_required"})
            msg_status = query.get("status", [None])[0]
            try:
                limit = int(query.get("limit", ["50"])[0])
            except ValueError:
                limit = 50
            messages = STORE.list_messages(tenant_id=tenant_id, user_id=user_id, status=msg_status, limit=limit)
            payload = {
                "messages": [
                    {
                        "message_id": m.message_id,
                        "tenant_id": m.tenant_id,
                        "user_id": m.user_id,
                        "category": m.category,
                        "channel": m.channel,
                        "subject": m.subject,
                        "body": m.body,
                        "event_id": m.event_id,
                        "status": m.status,
                        "created_at": m.created_at.isoformat(),
                        "delivered_at": m.delivered_at.isoformat() if m.delivered_at else None,
                    }
                    for m in messages
                ],
                "total": len(messages),
            }
            return self._send(200, payload)

        self._send(404, {"error": "not_found"})


def run(host: str = "0.0.0.0", port: int = 8095) -> None:
    server = HTTPServer((host, port), NotificationRequestHandler)
    print(f"Notification service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
