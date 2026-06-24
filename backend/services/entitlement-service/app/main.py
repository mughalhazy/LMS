from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

_ENT_EXEMPT = {"/health", "/metrics"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B08-002: HS256 JWT validation."""
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

from .models import EntitlementContext
from .schemas import IsEnabledRequest, ResolveRequest
from .service import EntitlementService
from .store import InMemoryPolicyStore, InMemoryRegistryReader

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()



POLICY_STORE = InMemoryPolicyStore()
REGISTRY = InMemoryRegistryReader()
SERVICE = EntitlementService(POLICY_STORE, REGISTRY)

# OA-004: ASGI shim — manifest now points to backend/services/entitlement-service with app.main:app
app = FastAPI(title="Entitlement Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "entitlement-service"}


@app.get("/metrics")
async def metrics():
    return {"service": "entitlement-service", "service_up": 1}


@app.post("/api/v1/entitlement/resolve")
async def resolve(http_request: Request, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    body = await http_request.json()
    ctx = _ctx_from_body(body)
    status_code, resp = SERVICE.resolve(ctx)
    return JSONResponse(status_code=status_code, content=resp)


@app.post("/api/v1/entitlement/is-enabled")
async def is_enabled(http_request: Request, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    body = await http_request.json()
    capability_key = body.get("capability_key", "")
    if not capability_key:
        return JSONResponse(status_code=400, content={"error": "capability_key_required"})
    ctx = _ctx_from_body(body)
    status_code, resp = SERVICE.is_enabled(ctx, capability_key)
    return JSONResponse(status_code=status_code, content=resp)


def _ctx_from_body(body: Dict[str, Any]) -> EntitlementContext:
    return EntitlementContext(
        tenant_id=body.get("tenant_id", ""),
        segment=body.get("segment", ""),
        plan=body.get("plan", ""),
        country=body.get("country", ""),
        add_ons=body.get("add_ons", []),
        policy_snapshot_version=body.get("policy_snapshot_version"),
        registry_snapshot_version=body.get("registry_snapshot_version"),
    )


class EntitlementRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _dispatch_post(self) -> Tuple[int, Dict[str, Any]]:
        body = self._read_json()

        if self.path == "/api/v1/entitlement/resolve":
            ctx = _ctx_from_body(body)
            return SERVICE.resolve(ctx)

        if self.path == "/api/v1/entitlement/is-enabled":
            ctx = _ctx_from_body(body)
            capability_key = body.get("capability_key", "")
            if not capability_key:
                return 400, {"error": "capability_key_required"}
            return SERVICE.is_enabled(ctx, capability_key)

        return 404, {"error": "not_found"}

    def do_POST(self) -> None:  # noqa: N802
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            status, payload = self._dispatch_post()
            self._send(status, payload)
        except (TypeError, KeyError) as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in _ENT_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "entitlement-service"})
            return
        if self.path == "/metrics":
            self._send(200, {"service": "entitlement-service", "service_up": 1})
            return
        self._send(404, {"error": "not_found"})


def run(host: str = "0.0.0.0", port: int = 8092) -> None:
    server = HTTPServer((host, port), EntitlementRequestHandler)
    print(f"Entitlement service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
