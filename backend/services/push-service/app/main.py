from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .schemas import (
    NotificationSendRequest,
    QueueDrainRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
)
from .service import PushService
from .store import InMemoryPushStore

STORE = InMemoryPushStore()
SERVICE = PushService(STORE)


class PushRequestHandler(BaseHTTPRequestHandler):
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
            if self.path == "/api/v1/push/subscriptions":
                status, payload = SERVICE.create_subscription(SubscriptionCreateRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/push/notifications":
                status, payload = SERVICE.send_notification(NotificationSendRequest(**body))
                return self._send(status, payload)

            if self.path == "/api/v1/push/queue/drain":
                status, payload = SERVICE.drain_queue(QueueDrainRequest(**body))
                return self._send(status, payload)

            self._send(404, {"error": "not_found"})
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            return self._send(200, {"status": "ok", "service": "push-service"})
        if self.path == "/metrics":
            return self._send(200, {"service": "push-service", "service_up": 1})

        parsed = urlparse(self.path)
        if parsed.path != "/api/v1/push/subscriptions":
            return self._send(404, {"error": "not_found"})

        query = parse_qs(parsed.query)
        tenant_id = query.get("tenant_id", [""])[0]
        user_id = query.get("user_id", [""])[0]
        if not tenant_id or not user_id:
            return self._send(400, {"error": "tenant_id_and_user_id_required"})

        status, payload = SERVICE.list_subscriptions(tenant_id, user_id)
        self._send(status, payload)

    def do_PATCH(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
            path_parts = self.path.split("/")
            if len(path_parts) == 6 and path_parts[:5] == ["", "api", "v1", "push", "subscriptions"]:
                subscription_id = path_parts[-1]
                status, payload = SERVICE.update_subscription(
                    subscription_id,
                    SubscriptionUpdateRequest(**body),
                )
                return self._send(status, payload)

            self._send(404, {"error": "not_found"})
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})


def run(host: str = "0.0.0.0", port: int = 8094) -> None:
    server = HTTPServer((host, port), PushRequestHandler)
    print(f"Push service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
