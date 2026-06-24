from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from .service import OwnerEconomicsService
from .store import InMemoryEconomicsStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryEconomicsStore()
SERVICE = OwnerEconomicsService(STORE)


class EconomicsHandler(BaseHTTPRequestHandler):
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
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "owner-economics-service"}); return
        if "/ledger/" in p:
            pid = p.split("/participants/")[1].split("/ledger")[0]
            period = self._qs("period")
            if period:
                self._send(*SERVICE.get_ledger(pid, tid, period)); return
            self._send(*SERVICE.list_ledgers(pid, tid)); return
        if "/payouts" in p:
            pid = p.split("/participants/")[1].split("/payouts")[0]
            self._send(*SERVICE.list_payouts(pid, tid)); return
        if p.startswith("/api/v1/teacher-economics/tutors/") and "/ledger" in p:
            tutor_id = p.split("/tutors/")[1].split("/ledger")[0]
            period = self._qs("period")
            if period:
                self._send(*SERVICE.teacher_view.get_teacher_ledger(tutor_id, tid, period)); return
            self._send(*SERVICE.teacher_view.list_teacher_entries(tutor_id, tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")
            if p == "/api/v1/owner-economics/earnings":
                self._send(*SERVICE.record_earning(body)); return
            if p == "/api/v1/owner-economics/payouts/calculate":
                self._send(*SERVICE.calculate_payout(body)); return
            if p == "/api/v1/teacher-economics/sessions":
                self._send(*SERVICE.teacher_view.record_session_earning(body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8098) -> None:
    server = HTTPServer((host, port), EconomicsHandler)
    print(f"Owner economics service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
