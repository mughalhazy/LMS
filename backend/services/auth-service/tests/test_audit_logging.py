from app.schemas import LoginRequest
from app.service import AuthService
from app.store import InMemoryAuthStore


def test_authentication_events_are_audited_with_required_fields() -> None:
    service = AuthService(InMemoryAuthStore(), signing_secret="test-secret")

    status, _ = service.login(LoginRequest(tenant_id="tenant-acme", email="admin@acme.test", password="AcmePass#123"))
    assert status == 200

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "authentication.login.succeeded"
    assert event.tenant_id == "tenant-acme"
    assert event.actor_id == "user-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
