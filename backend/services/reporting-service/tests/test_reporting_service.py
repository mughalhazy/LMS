from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["JWT_SHARED_SECRET"] = "test-secret"

from app.main import app


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _make_token() -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    payload = _b64url(json.dumps({"sub": "tester"}).encode("utf-8"))
    signing_input = f"{header}.{payload}".encode("utf-8")
    signature = _b64url(hmac.new(b"test-secret", signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {_make_token()}"}


def test_generate_compliance_report() -> None:
    response = client.post(
        "/reports/compliance",
        json={"tenant_id": "tenant-1", "department": "Operations"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()["report"]
    assert payload["envelope"]["report_type"] == "compliance"
    assert payload["envelope"]["row_count"] >= 1


def test_generate_course_completion_report() -> None:
    response = client.post("/reports/course-completion", json={"tenant_id": "tenant-1"}, headers=AUTH_HEADERS)
    assert response.status_code == 200
    payload = response.json()["report"]
    assert payload["envelope"]["report_type"] == "course_completion"
    assert len(payload["items"]) >= 1


def test_generate_analytics_dashboard() -> None:
    response = client.post(
        "/dashboards/analytics",
        json={"tenant_id": "tenant-1", "time_granularity": "week"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    dashboard = response.json()["dashboard"]
    assert dashboard["dashboard_id"] == "analytics-main"
    assert len(dashboard["widgets"]) == 4
    assert dashboard["widgets"][1]["widget_id"] == "sentiment_tracking"
    assert dashboard["widgets"][2]["trend_points"][-1]["value"] == 68.4


def test_export_csv_and_pdf() -> None:
    csv_response = client.post(
        "/exports",
        json={
            "tenant_id": "tenant-1",
            "report_type": "compliance",
            "report_id": "r-1",
            "format": "csv",
        },
        headers=AUTH_HEADERS,
    )
    assert csv_response.status_code == 200
    assert csv_response.json()["export"]["file_name"].endswith(".csv")

    pdf_response = client.post(
        "/exports",
        json={
            "tenant_id": "tenant-1",
            "report_type": "course_completion",
            "report_id": "r-2",
            "format": "pdf",
        },
        headers=AUTH_HEADERS,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.json()["export"]["content_type"] == "application/pdf"
