from fastapi.testclient import TestClient

from app.main import app, service


client = TestClient(app)


def auth_headers(
    role: str = "tenant_admin",
    principal_id: str = "admin-1",
    tenant_id: str = "t1",
    permissions: str = "org.user.invite,org.user.view,org.user.disable,org.role.assign",
) -> dict[str, str]:
    return {
        "X-Role": role,
        "X-Principal-Id": principal_id,
        "X-Tenant-Id": tenant_id,
        "X-Permissions": permissions,
    }


def setup_function() -> None:
    service.users.clear()


def create_user(tenant_id: str = "t1") -> str:
    response = client.post(
        "/users",
        json={
            "tenant_id": tenant_id,
            "email": f"{tenant_id}@example.com",
            "username": f"{tenant_id}-user",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "role_set": ["learner"],
            "auth_provider": "local",
            "created_by": "admin",
        },
        headers=auth_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200
    return response.json()["user"]["user_id"]


def test_user_lifecycle_and_profile_management() -> None:
    user_id = create_user()

    activate = client.post(
        f"/users/{user_id}/activate",
        json={"tenant_id": "t1", "activation_token": "token-123", "activated_by": "admin"},
        headers=auth_headers(),
    )
    assert activate.status_code == 200
    assert activate.json()["user"]["status"] == "active"

    profile = client.patch(
        f"/users/{user_id}/profile",
        json={"tenant_id": "t1", "updated_by": "admin", "department": "Engineering", "title": "Lead"},
        headers=auth_headers(),
    )
    assert profile.status_code == 200
    assert profile.json()["user"]["profile"]["department"] == "Engineering"

    prefs = client.put(
        f"/users/{user_id}/preferences",
        json={
            "tenant_id": "t1",
            "updated_by": "admin",
            "notification_preferences": {"email": True},
            "accessibility_preferences": {"contrast": "high"},
            "language_preference": "en-US",
        },
        headers=auth_headers(),
    )
    assert prefs.status_code == 200
    assert prefs.json()["preferences"]["language_preference"] == "en-US"


def test_tenant_scope_and_status_controls() -> None:
    user_id = create_user("tenant-a")

    wrong_tenant = client.get(
        f"/users/{user_id}?tenant_id=tenant-b",
        headers=auth_headers(tenant_id="tenant-a"),
    )
    assert wrong_tenant.status_code == 403

    status = client.post(
        f"/users/{user_id}/status",
        json={
            "tenant_id": "tenant-a",
            "target_status": "suspended",
            "reason_code": "policy",
            "changed_by": "security-admin",
        },
        headers=auth_headers(tenant_id="tenant-a"),
    )
    assert status.status_code == 200
    assert status.json()["user"]["status"] == "suspended"

    lock = client.post(
        f"/users/{user_id}/lock",
        json={"tenant_id": "tenant-a", "action": "lock", "reason_code": "risk", "performed_by": "soc"},
        headers=auth_headers(tenant_id="tenant-a"),
    )
    assert lock.status_code == 200
    assert lock.json()["user"]["status"] == "locked"


def test_identity_mapping_uniqueness_within_tenant() -> None:
    user1 = create_user("tenant-z")
    user2 = create_user("tenant-z")

    map_res = client.post(
        f"/users/{user1}/identity-links",
        json={
            "tenant_id": "tenant-z",
            "identity_provider": "okta",
            "external_subject_id": "sub-123",
            "mapped_by": "admin",
        },
        headers=auth_headers(tenant_id="tenant-z"),
    )
    assert map_res.status_code == 200

    conflict = client.post(
        f"/users/{user2}/identity-links",
        json={
            "tenant_id": "tenant-z",
            "identity_provider": "okta",
            "external_subject_id": "sub-123",
            "mapped_by": "admin",
        },
        headers=auth_headers(tenant_id="tenant-z"),
    )
    assert conflict.status_code == 409


def test_admin_only_routes_are_protected() -> None:
    user_id = create_user()

    response = client.post(
        f"/users/{user_id}/status",
        json={
            "tenant_id": "t1",
            "target_status": "suspended",
            "reason_code": "policy",
            "changed_by": "learner-1",
        },
        headers=auth_headers(
            role="learner",
            principal_id="learner-1",
            permissions="org.user.view",
        ),
    )
    assert response.status_code == 403
