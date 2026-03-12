from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from .service import NotificationService
from .store import InMemoryNotificationStore

STORE = InMemoryNotificationStore()
SERVICE = NotificationService(STORE)


class NotificationRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
            if self.path == "/api/v1/notifications/preferences":
                status, payload = SERVICE.upsert_preference(PreferenceUpsertRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/routes":
                status, payload = SERVICE.upsert_event_route(EventRouteUpsertRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/orchestrate":
                status, payload = SERVICE.orchestrate_notification(NotificationOrchestrationRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/events":
                status, payload = SERVICE.process_event(EventNotificationRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/notifications/deliveries/drain":
                status, payload = SERVICE.drain_delivery_queue(DeliveryDrainRequest(**body))
                return self._send(status, payload)

            self._send(404, {"error": "not_found"})
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except KeyError as exc:
            self._send(400, {"error": "template_render_error", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/v1/notifications/preferences":
            return self._send(404, {"error": "not_found"})

        query = parse_qs(parsed.query)
        tenant_id = query.get("tenant_id", [""])[0]
        user_id = query.get("user_id", [""])[0]
        if not tenant_id or not user_id:
            return self._send(400, {"error": "tenant_id_and_user_id_required"})

        status, payload = SERVICE.list_preferences(tenant_id, user_id)
        self._send(status, payload)


def run(host: str = "0.0.0.0", port: int = 8095) -> None:
    server = HTTPServer((host, port), NotificationRequestHandler)
    print(f"Notification service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
