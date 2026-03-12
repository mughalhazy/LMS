from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_compliance_report() -> None:
    response = client.post("/reports/compliance", json={"tenant_id": "tenant-1", "department": "Operations"})
    assert response.status_code == 200
    payload = response.json()["report"]
    assert payload["envelope"]["report_type"] == "compliance"
    assert payload["envelope"]["row_count"] >= 1


def test_generate_course_completion_report() -> None:
    response = client.post("/reports/course-completion", json={"tenant_id": "tenant-1"})
    assert response.status_code == 200
    payload = response.json()["report"]
    assert payload["envelope"]["report_type"] == "course_completion"
    assert len(payload["items"]) >= 1


def test_generate_analytics_dashboard() -> None:
    response = client.post("/dashboards/analytics", json={"tenant_id": "tenant-1", "time_granularity": "week"})
    assert response.status_code == 200
    dashboard = response.json()["dashboard"]
    assert dashboard["dashboard_id"] == "analytics-main"
    assert len(dashboard["widgets"]) == 2


def test_export_csv_and_pdf() -> None:
    csv_response = client.post(
        "/exports",
        json={
            "tenant_id": "tenant-1",
            "report_type": "compliance",
            "report_id": "r-1",
            "format": "csv",
        },
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
    )
    assert pdf_response.status_code == 200
    assert pdf_response.json()["export"]["content_type"] == "application/pdf"
