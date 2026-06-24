"""Service entrypoint — subscription-service HTTP API.

B10-006: subscription-service-design.md defines subscription lifecycle state management;
service.py (SubscriptionLifecycleService) has full implementation but no HTTP entrypoint existed.
"""
from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse
from uuid import uuid4

from .consumers import register_consumers as _register_consumers
from .models import Subscription, SubscriptionEvent, SubscriptionState
from .service import SubscriptionLifecycleService
from .errors import SubscriptionLifecycleError

_register_consumers()

_SVC = SubscriptionLifecycleService()
_STORE: dict[str, Subscription] = {}  # in-memory: subscription_id → Subscription

_SUB_EXEMPT = {"/health"}


def _jwt_valid(h: str | None) -> bool:
    """B10-006: HS256 JWT validation."""
    s = os.getenv("JWT_SHARED_SECRET")
    if not s:
        return True
    if not h or not h.startswith("Bearer "):
        return False
    tok = h[7:]
    try:
        a, p, g = tok.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        exp = _hmac.new(s.encode(), f"{a}.{p}".encode(), hashlib.sha256).digest()
        if not _hmac.compare_digest(exp, base64.urlsafe_b64decode(_pad(g))):
            return False
        pl = json.loads(base64.urlsafe_b64decode(_pad(p)))
        e = pl.get("exp")
        return e is None or float(e) >= time.time()
    except Exception:
        return False


def _serialize(sub: Subscription) -> Dict[str, Any]:
    def _ts(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None
    return {
        "subscription_id": sub.subscription_id,
        "tenant_id": sub.tenant_id,
        "plan_id": sub.plan_id,
        "state": sub.state.value,
        "active_enrollments": sub.active_enrollments,
        "segment_context": sub.segment_context,
        "trial_ends_at": _ts(sub.trial_ends_at),
        "current_period_ends_at": _ts(sub.current_period_ends_at),
        "activated_at": _ts(sub.activated_at),
        "expired_at": _ts(sub.expired_at),
        "cancelled_at": _ts(sub.cancelled_at),
        "grace_entered_at": _ts(sub.grace_entered_at),
        "suspended_at": _ts(sub.suspended_at),
        "updated_at": _ts(sub.updated_at),
        "lifecycle": [
            {"event": r.event.value, "from_state": r.from_state.value,
             "to_state": r.to_state.value, "timestamp": r.timestamp.isoformat()}
            for r in sub.lifecycle
        ],
    }


class SubscriptionHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) if length else b"{}")

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _SUB_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "subscription-service"}); return
        if p == "/metrics":
            self._send(200, {"service": "subscription-service", "service_up": 1,
                              "total_subscriptions": len(_STORE)}); return
        if p.startswith("/api/v1/subscriptions/"):
            sid = p.split("/api/v1/subscriptions/")[1]
            sub = _STORE.get(sid)
            if not sub or sub.tenant_id != tid:
                self._send(404, {"error": "subscription_not_found"}); return
            self._send(200, _serialize(sub)); return
        if p == "/api/v1/subscriptions":
            subs = [_serialize(s) for s in _STORE.values() if s.tenant_id == tid]
            self._send(200, {"subscriptions": subs, "total": len(subs)}); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")

            # Create subscription
            if p == "/api/v1/subscriptions":
                if not body.get("plan_id"):
                    self._send(400, {"error": "plan_id_required"}); return
                sub = Subscription(
                    subscription_id=f"sub_{uuid4().hex[:12]}",
                    tenant_id=tid,
                    plan_id=body["plan_id"],
                    segment_context=body.get("segment_context", {}),
                    state=SubscriptionState.TRIAL,
                )
                _STORE[sub.subscription_id] = sub
                self._send(201, _serialize(sub)); return

            # Lifecycle transitions
            if "/subscriptions/" in p:
                parts = p.split("/api/v1/subscriptions/")[1].split("/")
                sid = parts[0]
                action = parts[1] if len(parts) > 1 else None
                sub = _STORE.get(sid)
                if not sub or sub.tenant_id != tid:
                    self._send(404, {"error": "subscription_not_found"}); return

                event_map = {
                    "activate": SubscriptionEvent.ACTIVATION,
                    "renew": SubscriptionEvent.RENEWAL,
                    "expire": SubscriptionEvent.EXPIRATION,
                    "cancel": SubscriptionEvent.CANCELLATION,
                    "enter-grace": SubscriptionEvent.GRACE_ENTRY,
                    "suspend": SubscriptionEvent.SUSPENSION,
                }
                if action not in event_map:
                    self._send(404, {"error": "unknown_action"}); return
                try:
                    sub = _SVC.transition(sub, event_map[action])
                    _STORE[sid] = sub
                    self._send(200, _serialize(sub))
                except SubscriptionLifecycleError as exc:
                    self._send(409, {"error": "invalid_transition", "detail": str(exc)})
                return

            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8098) -> None:
    server = HTTPServer((host, port), SubscriptionHandler)
    print(f"Subscription service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
