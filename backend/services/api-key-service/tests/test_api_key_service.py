from app.schemas import (
    ApiKeyAuthorizeRequest,
    ApiKeyCreateRequest,
    ApiKeyRotateRequest,
    ApiKeyUsageReportRequest,
)
from app.service import ApiKeyService
from app.store import InMemoryApiKeyStore


def make_service() -> ApiKeyService:
    return ApiKeyService(InMemoryApiKeyStore())


def test_create_authorize_and_usage_tracking() -> None:
    service = make_service()

    status, payload = service.create_api_key(
        ApiKeyCreateRequest(
            tenant_id="tenant-acme",
            name="hris-sync",
            scopes=["integrations:hris.sync"],
            created_by="admin@acme.test",
        )
    )
    assert status == 201
    assert payload["api_key"].startswith("lms_")

    status, auth_payload = service.authorize(
        ApiKeyAuthorizeRequest(
            tenant_id="tenant-acme",
            api_key=payload["api_key"],
            required_scope="integrations:hris.sync",
        )
    )
    assert status == 200
    assert auth_payload["authorized"] is True

    status, usage_payload = service.usage_report(
        ApiKeyUsageReportRequest(
            tenant_id="tenant-acme",
            key_id=payload["key_id"],
        )
    )
    assert status == 200
    assert usage_payload["total_requests"] == 1
    assert usage_payload["per_scope"]["integrations:hris.sync"] == 1


def test_rotation_revokes_previous_key() -> None:
    service = make_service()

    _, create_payload = service.create_api_key(
        ApiKeyCreateRequest(
            tenant_id="tenant-acme",
            name="crm-upsert",
            scopes=["integrations:crm.upsert"],
            created_by="admin@acme.test",
        )
    )

    status, rotate_payload = service.rotate_api_key(
        ApiKeyRotateRequest(
            tenant_id="tenant-acme",
            key_id=create_payload["key_id"],
            rotated_by="secops@acme.test",
        )
    )
    assert status == 200

    status, _ = service.authorize(
        ApiKeyAuthorizeRequest(
            tenant_id="tenant-acme",
            api_key=create_payload["api_key"],
            required_scope="integrations:crm.upsert",
        )
    )
    assert status == 401

    status, new_auth_payload = service.authorize(
        ApiKeyAuthorizeRequest(
            tenant_id="tenant-acme",
            api_key=rotate_payload["api_key"],
            required_scope="integrations:crm.upsert",
        )
    )
    assert status == 200
    assert new_auth_payload["authorized"] is True


def test_authorization_rejects_insufficient_scope() -> None:
    service = make_service()

    _, payload = service.create_api_key(
        ApiKeyCreateRequest(
            tenant_id="tenant-acme",
            name="webhook-publisher",
            scopes=["integrations:webhooks.publish"],
            created_by="admin@acme.test",
        )
    )

    status, auth_payload = service.authorize(
        ApiKeyAuthorizeRequest(
            tenant_id="tenant-acme",
            api_key=payload["api_key"],
            required_scope="integrations:lti.launch",
        )
    )
    assert status == 403
    assert auth_payload["error"] == "insufficient_scope"
