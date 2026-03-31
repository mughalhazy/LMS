from fastapi.testclient import TestClient

from app.main import app, service


client = TestClient(app)


def _headers(tenant: str = "tenant-a") -> dict[str, str]:
    return {"X-Tenant-Id": tenant}


def test_program_lifecycle_and_mapping_flow() -> None:
    created = client.post(
        "/api/v1/programs",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "institution_id": "inst-1",
            "code": "DS-FOUND-2026",
            "title": "Data Science Foundations",
            "description": "Core path",
            "visibility": "institution",
            "metadata": {"level": "beginner"},
            "created_by": "user-1",
        },
    )
    assert created.status_code == 201
    program_id = created.json()["program_id"]

    mapped = client.put(
        f"/api/v1/programs/{program_id}/courses",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "updated_by": "user-2",
            "courses": [
                {"course_id": "c-101", "sequence_order": 1, "is_required": True, "minimum_completion_pct": 80},
                {"course_id": "c-205", "sequence_order": 2, "is_required": False},
            ],
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["mapping_version"] == 1

    transitioned = client.post(
        f"/api/v1/programs/{program_id}/status",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "target_status": "active",
            "change_reason": "approved",
            "changed_by": "admin-1",
        },
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["to_status"] == "active"

    detail = client.get(f"/api/v1/programs/{program_id}", headers=_headers())
    assert detail.status_code == 200
    assert len(detail.json()["mapped_courses"]) == 2


def test_tenant_isolation_mismatch_rejected() -> None:
    response = client.post(
        "/api/v1/programs",
        headers=_headers("tenant-z"),
        json={
            "tenant_id": "tenant-a",
            "institution_id": "inst-1",
            "code": "SEC-ERR",
            "title": "Mismatch",
            "created_by": "user-1",
        },
    )
    assert response.status_code == 403


def test_course_validation_and_activation_gate() -> None:
    created = client.post(
        "/api/v1/programs",
        headers=_headers("tenant-b"),
        json={
            "tenant_id": "tenant-b",
            "institution_id": "inst-2",
            "code": "ACT-GATE",
            "title": "Activation Gate",
            "created_by": "user-1",
        },
    )
    program_id = created.json()["program_id"]

    transition = client.post(
        f"/api/v1/programs/{program_id}/status",
        headers=_headers("tenant-b"),
        json={
            "tenant_id": "tenant-b",
            "target_status": "active",
            "change_reason": "try-activate",
            "changed_by": "admin",
        },
    )
    assert transition.status_code == 400

    bad_map = client.put(
        f"/api/v1/programs/{program_id}/courses",
        headers=_headers("tenant-b"),
        json={
            "tenant_id": "tenant-b",
            "updated_by": "user-2",
            "courses": [{"course_id": "missing-course", "sequence_order": 1, "is_required": True}],
        },
    )
    assert bad_map.status_code == 422


def test_observability_and_events_and_audit() -> None:
    create = client.post(
        "/api/v1/programs",
        headers=_headers("tenant-c"),
        json={
            "tenant_id": "tenant-c",
            "institution_id": "inst-3",
            "code": "OBS-01",
            "title": "Observability",
            "created_by": "user-1",
        },
    )
    assert create.status_code == 201
    assert service.observability.snapshot().get("program_create_total", 0) >= 1
    assert any(evt.event_type == "lms.program.program_created.v1" for evt in service.event_publisher.list_events())
    assert any(evt.event_type == "program.creation" for evt in service.audit_logger.list_events())


def test_correlation_id_propagates_to_events_and_audit_and_is_auto_generated() -> None:
    explicit_correlation_id = "corr-program-123"
    create = client.post(
        "/api/v1/programs",
        headers={**_headers("tenant-d"), "X-Correlation-Id": explicit_correlation_id},
        json={
            "tenant_id": "tenant-d",
            "institution_id": "inst-4",
            "code": "CORR-EXPLICIT",
            "title": "Correlation Explicit",
            "created_by": "user-1",
        },
    )
    assert create.status_code == 201

    assert any(
        evt.event_type == "lms.program.program_created.v1" and evt.correlation_id == explicit_correlation_id
        for evt in service.event_publisher.list_events()
    )
    assert any(
        evt.event_type == "program.creation" and evt.correlation_id == explicit_correlation_id
        for evt in service.audit_logger.list_events()
    )

    generated = client.post(
        "/api/v1/programs",
        headers=_headers("tenant-e"),
        json={
            "tenant_id": "tenant-e",
            "institution_id": "inst-5",
            "code": "CORR-GENERATED",
            "title": "Correlation Generated",
            "created_by": "user-1",
        },
    )
    assert generated.status_code == 201

    generated_event = next(
        evt
        for evt in reversed(service.event_publisher.list_events())
        if evt.event_type == "lms.program.program_created.v1" and evt.payload.get("program_id") == generated.json()["program_id"]
    )
    generated_audit = next(
        evt
        for evt in reversed(service.audit_logger.list_events())
        if evt.event_type == "program.creation" and evt.details.get("program_id") == generated.json()["program_id"]
    )
    assert generated_event.correlation_id
    assert generated_audit.correlation_id
    assert generated_event.correlation_id == generated_audit.correlation_id
