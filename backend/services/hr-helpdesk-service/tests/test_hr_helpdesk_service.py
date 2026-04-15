from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _headers(tenant: str = "tenant-hr") -> dict[str, str]:
    return {"X-Tenant-Id": tenant}


def test_helpdesk_advanced_flow_prioritization_analytics_and_automation() -> None:
    hook = client.post(
        "/api/v1/hr-helpdesk/automation/hooks",
        headers=_headers(),
        json={
            "tenant_id": "tenant-hr",
            "name": "Urgent escalation",
            "callback_target": "workflow://hr-escalation",
            "trigger": "priority_changed",
            "min_priority": "high",
        },
    )
    assert hook.status_code == 201

    created = client.post(
        "/api/v1/hr-helpdesk/tickets",
        headers=_headers(),
        json={
            "tenant_id": "tenant-hr",
            "employee_id": "emp-100",
            "subject": "Payroll missing for team",
            "description": "Five employees reported payroll underpayment after the latest pay cycle.",
            "category": "payroll",
            "urgency_level": 5,
            "impacted_employee_count": 5,
            "requested_by_manager": True,
            "due_at": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
            "tags": ["payroll", "quarter-close"],
        },
    )
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["priority"] == "urgent"
    assert ticket["priority_factors"]["sla_risk"] == 18.0
    ticket_id = ticket["ticket_id"]

    updated = client.patch(
        f"/api/v1/hr-helpdesk/tickets/{ticket_id}",
        headers=_headers(),
        json={
            "tenant_id": "tenant-hr",
            "updated_by": "hr-agent-1",
            "assigned_to": "hr-agent-1",
            "status": "in_progress",
            "urgency_level": 4,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["assigned_to"] == "hr-agent-1"
    assert updated.json()["first_response_at"] is not None

    queue = client.get("/api/v1/hr-helpdesk/queue", headers=_headers())
    assert queue.status_code == 200
    assert queue.json()["items"][0]["ticket_id"] == ticket_id
    assert queue.json()["items"][0]["priority_factors"]["manager_escalation"] == 8.0

    dispatches = client.get(
        "/api/v1/hr-helpdesk/automation/dispatches",
        headers=_headers(),
    )
    assert dispatches.status_code == 200
    assert dispatches.json()["total"] >= 1

    analytics = client.get("/api/v1/hr-helpdesk/analytics", headers=_headers())
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["totals"]["tickets"] == 1
    assert body["sla"]["at_risk_count"] == 1
    assert body["automation"]["configured_hooks"] == 1
    assert body["queue_insights"]["highest_priority_ticket_id"] == ticket_id


def test_reopen_and_tenant_isolation_behavior() -> None:
    created = client.post(
        "/api/v1/hr-helpdesk/tickets",
        headers=_headers("tenant-x"),
        json={
            "tenant_id": "tenant-x",
            "employee_id": "emp-200",
            "subject": "Benefits enrollment issue",
            "description": "Open enrollment submission is stuck in review and cannot be completed.",
            "category": "benefits",
            "urgency_level": 3,
            "impacted_employee_count": 1,
            "requested_by_manager": False,
        },
    )
    assert created.status_code == 201
    ticket_id = created.json()["ticket_id"]

    resolve = client.patch(
        f"/api/v1/hr-helpdesk/tickets/{ticket_id}",
        headers=_headers("tenant-x"),
        json={
            "tenant_id": "tenant-x",
            "updated_by": "agent-1",
            "status": "resolved",
            "resolution_summary": "Enrollment sync retried successfully.",
        },
    )
    assert resolve.status_code == 200

    reopened = client.patch(
        f"/api/v1/hr-helpdesk/tickets/{ticket_id}",
        headers=_headers("tenant-x"),
        json={
            "tenant_id": "tenant-x",
            "updated_by": "agent-2",
            "status": "in_progress",
        },
    )
    assert reopened.status_code == 200
    assert reopened.json()["reopened_count"] == 1

    forbidden = client.get("/api/v1/hr-helpdesk/tickets", headers=_headers("tenant-y"))
    assert forbidden.status_code == 200
    assert forbidden.json()["total"] == 0

    mismatch = client.patch(
        f"/api/v1/hr-helpdesk/tickets/{ticket_id}",
        headers=_headers("tenant-y"),
        json={
            "tenant_id": "tenant-y",
            "updated_by": "agent-3",
            "status": "closed",
        },
    )
    assert mismatch.status_code == 404
