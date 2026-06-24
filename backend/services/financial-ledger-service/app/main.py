from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

_FL_EXEMPT = {"/health"}
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
        pl = json.loads(base64.urlsafe_b64decode(_pad(p)))
        e = pl.get("exp"); return e is None or float(e) >= time.time()
    except Exception: return False

from .service import FinancialLedgerService

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


SERVICE = FinancialLedgerService()


class LedgerHandler(BaseHTTPRequestHandler):
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
        if p not in _FL_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "financial-ledger-service"}); return
        if "/students/" in p and p.endswith("/balance"):
            sid = p.split("/students/")[1].replace("/balance", "")
            self._send(*SERVICE.get_balance(sid, tid)); return
        if "/students/" in p and p.endswith("/entries"):
            sid = p.split("/students/")[1].replace("/entries", "")
            self._send(*SERVICE.list_entries(sid, tid)); return
        if "/students/" in p and p.endswith("/obligations"):
            sid = p.split("/students/")[1].replace("/obligations", "")
            self._send(*SERVICE.list_obligations(sid, tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/ledger/entries":
                self._send(*SERVICE.record_entry(body)); return
            if p == "/api/v1/ledger/obligations":
                self._send(*SERVICE.add_obligation(body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8105) -> None:
    server = HTTPServer((host, port), LedgerHandler)
    print(f"Financial ledger service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
