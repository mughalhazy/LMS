from __future__ import annotations

import base64, hashlib, hmac as _hmac, json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

_IB_EXEMPT = {"/health"}
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

from .service import BillingService
from .store import InMemoryBillingStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryBillingStore()
SERVICE = BillingService(STORE)


class BillingHandler(BaseHTTPRequestHandler):
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
        if p not in _IB_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "invoice-billing-service"}); return
        if p.startswith("/api/v1/billing-accounts/"):
            aid = p.split("/api/v1/billing-accounts/")[1]
            self._send(*SERVICE.get_billing_account(aid, tid)); return
        if p.startswith("/api/v1/invoices/"):
            iid = p.split("/api/v1/invoices/")[1]
            self._send(*SERVICE.get_invoice(iid, tid)); return
        if p == "/api/v1/invoices":
            self._send(*SERVICE.list_invoices(tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")
            actor = body.get("actor_id", "system")
            if p == "/api/v1/billing-accounts":
                self._send(*SERVICE.create_billing_account(body)); return
            if p == "/api/v1/invoices":
                self._send(*SERVICE.create_invoice(body)); return
            if p.endswith("/validate"):
                iid = p.split("/api/v1/invoices/")[1].replace("/validate", "")
                self._send(*SERVICE.validate_invoice(iid, tid)); return
            if p.endswith("/issue"):
                iid = p.split("/api/v1/invoices/")[1].replace("/issue", "")
                self._send(*SERVICE.issue_invoice(iid, tid, actor)); return
            if p.endswith("/void"):
                iid = p.split("/api/v1/invoices/")[1].replace("/void", "")
                self._send(*SERVICE.void_invoice(iid, tid, actor)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8096) -> None:
    server = HTTPServer((host, port), BillingHandler)
    print(f"Invoice billing service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
