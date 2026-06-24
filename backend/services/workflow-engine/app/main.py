from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from .service import WorkflowEngineService
from .store import InMemoryWorkflowStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryWorkflowStore()
SERVICE = WorkflowEngineService(STORE)


class WorkflowHandler(BaseHTTPRequestHandler):
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
            self._send(200, {"status": "ok", "service": "workflow-engine"}); return
        if p == "/api/v1/workflow/templates":
            self._send(*SERVICE.list_templates()); return
        if p.startswith("/api/v1/workflow/executions/"):
            eid = p.split("/executions/")[1]
            self._send(*SERVICE.get_execution(eid)); return
        if p == "/api/v1/workflow/executions":
            tid = self.headers.get("X-Tenant-Id", "")
            self._send(*SERVICE.list_executions(tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        try:
            body = self._read_json()
            if p == "/api/v1/workflow/templates":
                self._send(*SERVICE.register_template(body)); return
            if p == "/api/v1/workflow/trigger":
                self._send(*SERVICE.trigger(
                    body.get("event_trigger", ""),
                    body.get("tenant_id", ""),
                    body.get("payload", {}),
                )); return
            if p.endswith("/enable"):
                tid = p.split("/templates/")[1].replace("/enable", "")
                self._send(*SERVICE.enable_template(tid, body.get("enabled", True))); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8102) -> None:
    server = HTTPServer((host, port), WorkflowHandler)
    print(f"Workflow engine listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
