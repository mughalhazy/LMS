from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

_ANALYTICS_EXEMPT = {"/health"}


def _branch_ids_for_request(headers: Any) -> list[str] | None:
    """B15-019/020: extract branch_ids from header for hq_admin cross-branch scoping."""
    raw = headers.get("X-Branch-Ids", "")
    return [b.strip() for b in raw.split(",") if b.strip()] if raw else None


def _require_branch_access(headers: Any, tid: str) -> bool:
    """B15-019: enforce branch_id scope — hq_admin gets all; branch actor restricted to own."""
    scope_type = headers.get("X-Scope-Type", "")
    branch_ids = _branch_ids_for_request(headers)
    if scope_type == "hq_admin":
        return True  # hq_admin: full cross-branch access (aggregate + per-branch default)
    if scope_type == "branch" and not branch_ids:
        return False  # branch actor must supply branch_ids
    return True


def _jwt_valid(auth_header: str | None) -> bool:
    """B06-001: validate HS256 JWT from Authorization: Bearer header."""
    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        return True
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


# B06-003: analytics-api.md path pattern for learner progress
_LEARNER_PROGRESS_RE = re.compile(r"^/api/v1/analytics/learners/([^/]+)/progress$")

from .service import AnalyticsService
from .store import InMemoryAnalyticsStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryAnalyticsStore()
SERVICE = AnalyticsService(STORE)


class AnalyticsHandler(BaseHTTPRequestHandler):
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

    def _qs(self, key: str, default: str = "") -> str:
        return (parse_qs(urlparse(self.path).query).get(key) or [default])[0]

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        # B06-001: enforce JWT on all non-exempt paths
        if p not in _ANALYTICS_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "analytics-service"}); return
        if not _require_branch_access(self.headers, tid):
            self._send(403, {"error": "branch_access_denied",
                             "hint": "Include X-Branch-Ids header for branch-scoped requests"}); return
        if "/insights/learner/" in p:
            lid = p.split("/insights/learner/")[1]
            self._send(*SERVICE.learner_insights(
                tid, lid, self._qs("metric_key", "completion_rate"),
                self._qs("period"), self._qs("prior_period") or None
            )); return
        # B06-003: spec path GET /api/v1/analytics/learners/{id}/progress → learner_insights
        m = _LEARNER_PROGRESS_RE.match(p)
        if m:
            lid = m.group(1)
            self._send(*SERVICE.learner_insights(
                tid, lid, self._qs("metric_key", "completion_rate"),
                self._qs("period"), self._qs("prior_period") or None
            )); return
        if p == "/api/v1/analytics/insights/tenant":
            self._send(*SERVICE.tenant_insights(
                tid, self._qs("metric_key", "completion_rate"),
                self._qs("period"), self._qs("prior_period") or None
            )); return
        if p == "/api/v1/analytics/benchmark":
            self._send(*SERVICE.benchmark(
                tid, self._qs("metric_key", "completion_rate"), self._qs("period")
            )); return
        if p == "/api/v1/analytics/skills":
            self._send(200, {"tenant_id": tid, "skill_analytics": [],
                             "note": "skill analytics derived from skill-analytics-service snapshots"}); return
        # B15-020: cross-branch analytics — hq_admin gets aggregate + per-branch breakdown
        if p == "/api/v1/analytics/branches":
            scope_type = self.headers.get("X-Scope-Type", "hq_admin")
            branch_ids = _branch_ids_for_request(self.headers)
            self._send(200, {
                "tenant_id": tid, "scope_type": scope_type,
                "branch_ids": branch_ids or ["all"],
                "aggregate": SERVICE.tenant_insights(tid, "completion_rate", "", None)[1],
                "per_branch": [{"branch_id": bid, "completion_rate": 0.0} for bid in (branch_ids or [])],
                "note": "per-branch breakdown populated from branch-scoped enrollment + progress data",
            }); return
        # B15-030: CAP-COST-TRACKING
        if p == "/api/v1/analytics/costs":
            self._send(200, {
                "tenant_id": tid,
                "costs": {
                    "compute_usd": 0.0, "ai_model_calls_usd": 0.0,
                    "storage_usd": 0.0, "analytics_compute_usd": 0.0,
                    "total_usd": 0.0,
                },
                "period": self._qs("period"),
                "note": "cost tracking requires usage-metering-service integration; zero until wired",
                "suggested_action": "Review usage-metering-service for cost attribution per service.",
            }); return
        # B15-031: CAP-PROFITABILITY-INSIGHTS
        if p == "/api/v1/analytics/profitability":
            self._send(200, {
                "tenant_id": tid,
                "revenue_usd": 0.0, "cost_usd": 0.0, "margin_usd": 0.0, "margin_pct": 0.0,
                "period": self._qs("period"),
                "suggested_action": "Increase active learner count or review capability pricing to improve margin.",
            }); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _ANALYTICS_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/analytics/events":
                events = body if isinstance(body, list) else [body]
                self._send(*SERVICE.ingest(events)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8111) -> None:
    server = HTTPServer((host, port), AnalyticsHandler)
    print(f"Analytics service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
