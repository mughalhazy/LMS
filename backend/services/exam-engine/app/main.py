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

from .service import ExamEngineService
from .store import InMemoryExamStore

_EXAM_EXEMPT_PATHS = {"/health", "/metrics"}


def _jwt_valid(auth_header: str | None) -> bool:
    """B03-004: validate HS256 JWT from Authorization: Bearer header."""
    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        return True  # dev/test mode — secret not configured
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    try:
        h, p, s = token.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        expected = _hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        received = base64.urlsafe_b64decode(_pad(s))
        if not _hmac.compare_digest(expected, received):
            return False
        payload = json.loads(base64.urlsafe_b64decode(_pad(p)))
        exp = payload.get("exp")
        return exp is None or float(exp) >= time.time()
    except Exception:
        return False

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryExamStore()
SERVICE = ExamEngineService(STORE)


class ExamHandler(BaseHTTPRequestHandler):
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
        # B03-004: enforce JWT on all non-exempt paths
        if p not in _EXAM_EXEMPT_PATHS and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "exam-engine"}); return
        if p.startswith("/api/v1/exam/sessions/"):
            sid = p.split("/sessions/")[1]
            self._send(*SERVICE.get_session(sid, tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        # B03-004: enforce JWT on all non-exempt paths
        if p not in _EXAM_EXEMPT_PATHS and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")
            if p == "/api/v1/exam/exams":
                self._send(*SERVICE.register_exam(body)); return
            if p == "/api/v1/exam/sessions":
                self._send(*SERVICE.start_exam(body)); return
            if p.endswith("/answers"):
                sid = p.split("/sessions/")[1].replace("/answers", "")
                self._send(*SERVICE.submit_answer(sid, tid, body)); return
            if p.endswith("/submit"):
                sid = p.split("/sessions/")[1].replace("/submit", "")
                self._send(*SERVICE.submit_exam(sid, tid)); return
            if p.endswith("/proctor-events"):
                sid = p.split("/sessions/")[1].replace("/proctor-events", "")
                self._send(*SERVICE.record_proctor_event(sid, tid, body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8110) -> None:
    server = HTTPServer((host, port), ExamHandler)
    print(f"Exam engine listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
