from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from .service import AuditPolicyService
from .store import InMemoryAuditStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryAuditStore()
SERVICE = AuditPolicyService(STORE)


class AuditHandler(BaseHTTPRequestHandler):
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

    def _read_json(self) -> Any:
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
            self._send(200, {"status": "ok", "service": "audit-policy-service"}); return
        if p == "/api/v1/audit/records":
            self._send(*SERVICE.query_audit(tid, self._qs("event_type") or None)); return
        if p == "/api/v1/audit/export":
            actor_role = self.headers.get("X-Actor-Role", "auditor")
            self._send(*SERVICE.export_evidence_verified(
                tid, actor_role, self._qs("from") or None, self._qs("to") or None)); return
        if p == "/api/v1/audit/taxonomy":
            self._send(*SERVICE.get_taxonomy()); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        try:
            body = self._read_json()
            tid = body.get("tenant_id", self.headers.get("X-Tenant-Id", ""))
            if p == "/api/v1/policy/evaluate":
                self._send(*SERVICE.evaluate(body)); return
            if p == "/api/v1/policy/evaluate-batch":
                reqs = body if isinstance(body, list) else body.get("requests", [])
                self._send(*SERVICE.evaluate_batch(reqs)); return
            if p == "/api/v1/policy/bundles":
                self._send(*SERVICE.publish_bundle_verified(body)); return
            if p == "/api/v1/audit/events":
                self._send(*SERVICE.ingest_audit_event(body)); return
            if p == "/api/v1/audit/taxonomy/event-types":
                self._send(*SERVICE.add_event_type(body.get("event_type", ""), tid)); return
            if p == "/api/v1/audit/retention/legal-hold":
                self._send(*SERVICE.set_legal_hold(
                    tid, body.get("record_ids", []), body.get("reason", ""))); return
            if p == "/api/v1/audit/retention/class":
                self._send(*SERVICE.apply_retention_class(
                    tid, body.get("record_ids", []), body.get("retention_class", "standard"))); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8101) -> None:
    server = HTTPServer((host, port), AuditHandler)
    print(f"Audit policy service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
