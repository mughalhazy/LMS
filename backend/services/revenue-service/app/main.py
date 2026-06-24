from __future__ import annotations

import base64, hashlib, hmac as _hmac, json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

_REV_EXEMPT = {"/health"}
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

from .service import RevenueService
from .store import InMemoryRevenueStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryRevenueStore()
SERVICE = RevenueService(STORE)


class RevenueHandler(BaseHTTPRequestHandler):
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

    def _qs(self, key: str) -> str:
        return (parse_qs(urlparse(self.path).query).get(key) or [""])[0]

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _REV_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if p == "/health":
            self._send(200, {"status": "ok", "service": "revenue-service"}); return
        if p.startswith("/api/v1/revenue/tenants/"):
            tid = p.split("/api/v1/revenue/tenants/")[1]
            self._send(*SERVICE.query_tenant(tid, self._qs("from"), self._qs("to"))); return
        if p == "/api/v1/revenue/tenant-capability":
            self._send(*SERVICE.query_tenant_capability_matrix(
                self.headers.get("X-Tenant-Id", ""), self._qs("from"), self._qs("to"))); return
        if p.startswith("/api/v1/revenue/snapshots/"):
            as_of = p.split("/api/v1/revenue/snapshots/")[1]
            self._send(*SERVICE.get_revenue_snapshot(as_of)); return
        if p.startswith("/api/v1/revenue/capabilities/"):
            ck = p.split("/api/v1/revenue/capabilities/")[1]
            if self._qs("monthly") == "true":
                self._send(*SERVICE.query_capability_monthly(ck, self._qs("from"), self._qs("to"))); return
            self._send(*SERVICE.query_capability(ck, self._qs("from"), self._qs("to"))); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/revenue/facts":
                result = SERVICE.ingest_fact(body)
                SERVICE.check_anomalies(body.get("tenant_id", ""))
                self._send(*result); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8097) -> None:
    server = HTTPServer((host, port), RevenueHandler)
    print(f"Revenue service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
