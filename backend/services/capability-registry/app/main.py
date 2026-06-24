from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

_CR_EXEMPT = {"/health", "/metrics"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B08-003: HS256 JWT validation."""
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

from .service import CapabilityRegistryService
from .store import InMemoryCapabilityStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()



STORE = InMemoryCapabilityStore()
SERVICE = CapabilityRegistryService(STORE)

# OA-004: ASGI shim — manifest now points to backend/services/capability-registry with app.main:app
app = FastAPI(title="Capability Registry", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "capability-registry"}


@app.get("/metrics")
async def metrics():
    return {"service": "capability-registry", "service_up": 1}


@app.get("/api/v1/capability-registry")
async def list_capabilities(snapshot_version: Optional[str] = None, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.list_capabilities(snapshot_version)
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/capability-registry/graph")
async def get_dependency_graph(snapshot_version: Optional[str] = None, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.get_dependency_graph(snapshot_version)
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/capability-registry/snapshot/{version}")
async def get_snapshot(version: str, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.get_snapshot(version)
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/capability-registry/{key}")
async def get_capability(key: str, snapshot_version: Optional[str] = None, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.get_capability(key, snapshot_version)
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/v1/capability-registry/draft")
async def submit_draft(body: Dict[str, Any], authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, resp = SERVICE.submit_draft(
        created_by=body.get("created_by", ""),
        changes=body.get("changes", []),
    )
    return JSONResponse(status_code=status_code, content=resp)


@app.post("/api/v1/capability-registry/draft/{draft_id}/publish")
async def publish_draft(draft_id: str, authorization: Optional[str] = Header(None)):
    if not _jwt_valid(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    status_code, body = SERVICE.publish_draft(draft_id)
    return JSONResponse(status_code=status_code, content=body)


class CapabilityRegistryHandler(BaseHTTPRequestHandler):
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

    def _qs(self, key: str) -> str | None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        vals = params.get(key, [])
        return vals[0] if vals else None

    def _path_base(self) -> str:
        return urlparse(self.path).path

    def _dispatch_get(self) -> Tuple[int, Dict[str, Any]]:
        path = self._path_base()
        snap = self._qs("snapshot_version")

        if path == "/api/v1/capability-registry":
            return SERVICE.list_capabilities(snap)

        if path == "/api/v1/capability-registry/graph":
            return SERVICE.get_dependency_graph(snap)

        if path.startswith("/api/v1/capability-registry/snapshot/"):
            version = path.split("/api/v1/capability-registry/snapshot/", 1)[1]
            return SERVICE.get_snapshot(version)

        if path.startswith("/api/v1/capability-registry/"):
            key = path.split("/api/v1/capability-registry/", 1)[1]
            if key and "/" not in key:
                return SERVICE.get_capability(key, snap)

        return 404, {"error": "not_found"}

    def _dispatch_post(self) -> Tuple[int, Dict[str, Any]]:
        path = self._path_base()
        body = self._read_json()

        if path == "/api/v1/capability-registry/draft":
            return SERVICE.submit_draft(
                created_by=body.get("created_by", ""),
                changes=body.get("changes", []),
            )

        if path.startswith("/api/v1/capability-registry/draft/") and path.endswith("/publish"):
            draft_id = path.split("/api/v1/capability-registry/draft/", 1)[1].replace("/publish", "")
            return SERVICE.publish_draft(draft_id)

        return 404, {"error": "not_found"}

    def do_GET(self) -> None:  # noqa: N802
        if self._path_base() not in _CR_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if self._path_base() == "/health":
            self._send(200, {"status": "ok", "service": "capability-registry"})
            return
        if self._path_base() == "/metrics":
            self._send(200, {"service": "capability-registry", "service_up": 1})
            return
        try:
            status, payload = self._dispatch_get()
            self._send(status, payload)
        except Exception as exc:
            self._send(500, {"error": "internal_error", "detail": str(exc)})

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


def run(host: str = "0.0.0.0", port: int = 8093) -> None:
    server = HTTPServer((host, port), CapabilityRegistryHandler)
    print(f"Capability registry listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
