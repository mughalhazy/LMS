from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from .service import OfflineSyncService

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


SERVICE = OfflineSyncService()


class OfflineHandler(BaseHTTPRequestHandler):
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
        uid = self.headers.get("X-User-Id", "")
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "offline-sync-service"}); return
        if p.startswith("/api/v1/offline/downloads/") and "/cursor" in p:
            dl_id = p.split("/downloads/")[1].split("/cursor")[0]
            self._send(*SERVICE.get_transfer_cursor(dl_id)); return
        if p == "/api/v1/offline/recovery-state":
            self._send(*SERVICE.get_recovery_state(uid, tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        try:
            body = self._read_json()
            if p == "/api/v1/offline/downloads":
                self._send(*SERVICE.request_download(body)); return
            if p == "/api/v1/offline/downloads/cursor":
                self._send(*SERVICE.advance_transfer_cursor(
                    body.get("download_id", ""), body.get("bytes_received", 0))); return
            if p == "/api/v1/offline/progress-events":
                self._send(*SERVICE.queue_progress_event_with_conflict_check(body)); return
            if p == "/api/v1/offline/operator-actions":
                self._send(*SERVICE.queue_operator_action(body)); return
            if p == "/api/v1/offline/operator-actions/lease":
                self._send(*SERVICE.lease_batch(body.get("tenant_id", ""), body.get("batch_size", 10))); return
            if p == "/api/v1/offline/operator-actions/acknowledge":
                self._send(*SERVICE.acknowledge(body.get("intent_id", ""), body.get("lease_id", ""))); return
            if p == "/api/v1/offline/operator-actions/reschedule":
                self._send(*SERVICE.reschedule(
                    body.get("intent_id", ""), body.get("lease_id", ""), body.get("backoff_seconds", 60))); return
            if p == "/api/v1/offline/sync":
                self._send(*SERVICE.sync(body.get("user_id", ""), body.get("tenant_id", ""))); return
            if p == "/api/v1/offline/sync/resume":
                self._send(*SERVICE.resume_sync(
                    body.get("user_id", ""), body.get("tenant_id", ""),
                    body.get("network_snapshot", {}))); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8107) -> None:
    server = HTTPServer((host, port), OfflineHandler)
    print(f"Offline sync service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
