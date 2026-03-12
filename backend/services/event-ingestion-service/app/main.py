from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple

from .schemas import EventIngestRequest
from .service import EventIngestionService
from .store import InMemoryEventStore

STORE = InMemoryEventStore(max_events_per_tenant=100000)
SERVICE = EventIngestionService(STORE)


class EventIngestionRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _dispatch_post(self) -> Tuple[int, Dict[str, Any]]:
        body = self._read_json()

        if self.path == "/api/v1/events/ingest":
            return SERVICE.ingest_event(EventIngestRequest(**body))

        if self.path == "/api/v1/events/ingest/batch":
            tenant_id = body.get("tenant_id", "")
            event_records = [EventIngestRequest(**item) for item in body.get("events", [])]
            return SERVICE.ingest_batch(tenant_id=tenant_id, events=event_records)

        return 404, {"error": "not_found"}

    def do_POST(self) -> None:  # noqa: N802
        try:
            status, payload = self._dispatch_post()
            self._send(status, payload)
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/v1/events/streams/"):
            tenant_id = self.path.rsplit("/", 1)[-1]
            status, payload = SERVICE.get_tenant_stream(tenant_id)
            self._send(status, payload)
            return

        if self.path == "/api/v1/events/metrics":
            status, payload = SERVICE.get_ingestion_metrics()
            self._send(status, payload)
            return

        self._send(404, {"error": "not_found"})


def run(host: str = "0.0.0.0", port: int = 8095) -> None:
    server = ThreadingHTTPServer((host, port), EventIngestionRequestHandler)
    print(f"Event ingestion service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
