from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_tenant_lifecycle_configuration_and_isolation() -> None:
    validate = client.post(
        "/api/v1/tenants/validate",
        json={"name": "Acme Inc", "country_code": "US", "segment_type": "enterprise", "plan_type": "enterprise"},
    )
    assert validate.status_code == 200
    assert validate.json()["validation_passed"] is True

    created = client.post(
        "/api/v1/tenants",
        json={
            "name": "Acme Inc",
            "country_code": "US",
            "segment_type": "enterprise",
            "plan_type": "enterprise",
            "addon_flags": ["ai_tutor"],
            "admin_user": "admin_1",
        },
    )
    assert created.status_code == 200
    tenant_id = created.json()["tenant_id"]
    assert created.json()["isolation_mode"] == "database_per_tenant"

    init_config = client.put(
        f"/api/v1/tenants/{tenant_id}/configuration",
        headers={"x-tenant-id": tenant_id},
        json={
            "default_locale": "en-US",
            "timezone": "UTC",
            "branding": {"theme": "dark"},
            "enabled_modules": ["catalog"],
            "security_baseline": {"security.require_mfa": True},
        },
    )
    assert init_config.status_code == 200
    assert init_config.json()["configuration"]["version"] == 1

    patched = client.patch(
        f"/api/v1/tenants/{tenant_id}/configuration",
        headers={"x-tenant-id": tenant_id},
        json={"config_patch": {"timezone": "America/New_York"}, "actor_id": "admin_1", "change_reason": "regional"},
    )
    assert patched.status_code == 200
    assert patched.json()["configuration"]["version"] == 2

    client.post(
        f"/api/v1/tenants/{tenant_id}/lifecycle/suspend",
        headers={"x-tenant-id": tenant_id},
        json={"suspension_reason": "billing_hold", "suspended_by": "system"},
    )

    denied = client.post(
        "/api/v1/isolation/evaluate",
        json={"tenant_id": tenant_id, "actor_tenant_id": tenant_id, "actor_id": "admin_1", "action": "write"},
    )
    assert denied.status_code == 200
    assert denied.json()["allowed"] is False

    cross_tenant = client.post(
        "/api/v1/isolation/evaluate",
        json={"tenant_id": tenant_id, "actor_tenant_id": "another_tenant", "actor_id": "admin_1", "action": "read"},
    )
    assert cross_tenant.status_code == 200
    assert cross_tenant.json()["allowed"] is False
