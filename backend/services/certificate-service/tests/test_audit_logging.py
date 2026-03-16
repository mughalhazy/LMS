from fastapi.testclient import TestClient

from app.main import AUDIT_LOGGER, app


client = TestClient(app)


def test_certificate_issuance_is_audited_with_required_fields() -> None:
    response = client.post(
        "/api/v1/certificates",
        json={"tenant_id": "tenant-a", "learner_id": "learner-1", "course_id": "course-1"},
    )
    assert response.status_code == 200
    event = AUDIT_LOGGER.list_events()[-1]
    assert event.event_type == "certificate.issuance"
    assert event.tenant_id == "tenant-a"
    assert event.actor_id == "learner-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
