from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from .service import SystemEconomicsService

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


SERVICE = SystemEconomicsService()


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

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p == "/health":
            self._send(200, {"status": "ok", "service": "system-economics-service"}); return
        if "/profitability/" in p:
            parts = p.split("/profitability/")[1].split("/")
            tid, period = parts[0], parts[1] if len(parts) > 1 else ""
            self._send(*SERVICE.get_profitability(tid, period)); return
        if "/insights/" in p:
            parts = p.split("/insights/")[1].split("/")
            tid, period = parts[0], parts[1] if len(parts) > 1 else ""
            self._send(*SERVICE.get_insights(tid, period)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        try:
            body = self._read_json()
            if p == "/api/v1/economics/costs":
                self._send(*SERVICE.record_cost(body)); return
            if p == "/api/v1/economics/revenue":
                self._send(*SERVICE.record_revenue(
                    body.get("tenant_id", ""), body.get("period", ""), float(body.get("revenue", 0))
                )); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8106) -> None:
    server = HTTPServer((host, port), EconomicsHandler)
    print(f"System economics service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
