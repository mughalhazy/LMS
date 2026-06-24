from __future__ import annotations

import base64, hashlib, hmac as _hmac, json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

_CO_EXEMPT = {"/health"}
def _jwt_valid(h: str | None) -> bool:
    s = os.getenv("JWT_SHARED_SECRET")
    if not s: return True
    if not h or not h.startswith("Bearer "): return False
    tok = h[7:]
    try:
        a, p, g = tok.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        exp = _hmac.new(s.encode(), f"{a}.{p}".encode(), hashlib.sha256).digest()
        if not _hmac.compare_digest(exp, base64.urlsafe_b64decode(_pad(g))): return False
        pl = json.loads(base64.urlsafe_b64decode(_pad(p))); e = pl.get("exp")
        return e is None or float(e) >= time.time()
    except Exception: return False

from .service import CheckoutService
from .store import InMemoryCheckoutStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryCheckoutStore()
SERVICE = CheckoutService(STORE)


class CheckoutHandler(BaseHTTPRequestHandler):
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
        if p not in _CO_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "checkout-service"}); return
        if p.startswith("/api/v1/checkout/sessions/") and not any(p.endswith(x) for x in ("/items", "/submit")):
            sid = p.split("/api/v1/checkout/sessions/")[1]
            self._send(*SERVICE.get_session(sid, tid)); return
        if p.startswith("/api/v1/checkout/orders/"):
            oid = p.split("/api/v1/checkout/orders/")[1]
            self._send(*SERVICE.get_order(oid, tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")
            if p == "/api/v1/checkout/sessions":
                self._send(*SERVICE.create_session(body)); return
            if p.endswith("/items"):
                sid = p.split("/api/v1/checkout/sessions/")[1].replace("/items", "")
                self._send(*SERVICE.update_items(sid, tid, body.get("items", []))); return
            if p.endswith("/submit"):
                sid = p.split("/api/v1/checkout/sessions/")[1].replace("/submit", "")
                self._send(*SERVICE.submit_session(sid, tid, body)); return
            if p.endswith("/initiate-payment"):
                oid = p.split("/api/v1/checkout/orders/")[1].replace("/initiate-payment", "")
                self._send(*SERVICE.initiate_payment(oid, tid, body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8095) -> None:
    server = HTTPServer((host, port), CheckoutHandler)
    print(f"Checkout service listening on http://{host}:{port}")
    server.serve_forever()


# GAP-007 / RISK-012: manifest entry is app.main:app (uvicorn ASGI).
# checkout-service uses stdlib HTTPServer; this shim exposes an ASGI `app`
# so the module is importable as app.main:app.
from fastapi import FastAPI as _FastAPI, Request as _Request
from fastapi.responses import JSONResponse as _JSONResponse

app = _FastAPI(title="Checkout Service", version="1.0.0", docs_url=None, openapi_url=None)


@app.api_route("/api/v1/checkout/{path:path}", methods=["GET", "POST"])
@app.api_route("/api/v1/checkout/orders/{path:path}", methods=["GET", "POST"])
@app.get("/health")
async def _asgi_checkout(request: _Request, path: str = "") -> _JSONResponse:
    """ASGI shim: delegates to stdlib CheckoutService via SERVICE."""
    method = request.method.upper()
    full_path = str(request.url.path)
    tid = request.headers.get("X-Tenant-Id", "")

    if full_path == "/health":
        return _JSONResponse({"status": "ok", "service": "checkout-service"})

    if not _jwt_valid(request.headers.get("Authorization")):
        return _JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        body = {}

    if method == "POST" and full_path == "/api/v1/checkout/sessions":
        status_code, result = SERVICE.create_session(body)
        return _JSONResponse(result, status_code=status_code)
    if method == "GET" and full_path.startswith("/api/v1/checkout/sessions/"):
        sid = full_path.split("/api/v1/checkout/sessions/")[1]
        status_code, result = SERVICE.get_session(sid, tid)
        return _JSONResponse(result, status_code=status_code)
    if method == "POST" and full_path.endswith("/items"):
        sid = full_path.split("/api/v1/checkout/sessions/")[1].replace("/items", "")
        status_code, result = SERVICE.update_items(sid, tid, body.get("items", []))
        return _JSONResponse(result, status_code=status_code)
    if method == "POST" and full_path.endswith("/submit"):
        sid = full_path.split("/api/v1/checkout/sessions/")[1].replace("/submit", "")
        status_code, result = SERVICE.submit_session(sid, tid, body)
        return _JSONResponse(result, status_code=status_code)
    if method == "GET" and full_path.startswith("/api/v1/checkout/orders/"):
        oid = full_path.split("/api/v1/checkout/orders/")[1]
        status_code, result = SERVICE.get_order(oid, tid)
        return _JSONResponse(result, status_code=status_code)
    if method == "POST" and full_path.endswith("/initiate-payment"):
        oid = full_path.split("/api/v1/checkout/orders/")[1].replace("/initiate-payment", "")
        status_code, result = SERVICE.initiate_payment(oid, tid, body)
        return _JSONResponse(result, status_code=status_code)
    return _JSONResponse({"error": "not_found"}, status_code=404)


if __name__ == "__main__":
    run()
