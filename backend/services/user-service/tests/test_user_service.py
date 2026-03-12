from fastapi.testclient import TestClient

from app.main import app, service


client = TestClient(app)


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
    )
    assert response.status_code == 200
    return response.json()["user"]["user_id"]


def test_user_lifecycle_and_profile_management() -> None:
    user_id = create_user()

    activate = client.post(
        f"/users/{user_id}/activate",
        json={"tenant_id": "t1", "activation_token": "token-123", "activated_by": "admin"},
    )
    assert activate.status_code == 200
    assert activate.json()["user"]["status"] == "active"

    profile = client.patch(
        f"/users/{user_id}/profile",
        json={"tenant_id": "t1", "updated_by": "admin", "department": "Engineering", "title": "Lead"},
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
    )
    assert prefs.status_code == 200
    assert prefs.json()["preferences"]["language_preference"] == "en-US"


def test_tenant_scope_and_status_controls() -> None:
    user_id = create_user("tenant-a")

    wrong_tenant = client.get(f"/users/{user_id}?tenant_id=tenant-b")
    assert wrong_tenant.status_code == 404

    status = client.post(
        f"/users/{user_id}/status",
        json={
            "tenant_id": "tenant-a",
            "target_status": "suspended",
            "reason_code": "policy",
            "changed_by": "security-admin",
        },
    )
    assert status.status_code == 200
    assert status.json()["user"]["status"] == "suspended"

    lock = client.post(
        f"/users/{user_id}/lock",
        json={"tenant_id": "tenant-a", "action": "lock", "reason_code": "risk", "performed_by": "soc"},
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
    )
    assert conflict.status_code == 409


def test_core_user_endpoints_patch_and_delete() -> None:
    user_id = create_user("tenant-core")

    patch_response = client.patch(
        f"/users/{user_id}",
        json={
            "tenant_id": "tenant-core",
            "updated_by": "admin",
            "username": "renamed-user",
            "role_set": ["admin"],
            "department": "Platform",
            "status": "active",
        },
    )
    assert patch_response.status_code == 200
    patched_user = patch_response.json()["user"]
    assert patched_user["username"] == "renamed-user"
    assert patched_user["role_set"] == ["admin"]
    assert patched_user["profile"]["department"] == "Platform"

    delete_response = client.delete(f"/users/{user_id}?tenant_id=tenant-core")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/users/{user_id}?tenant_id=tenant-core")
    assert get_deleted.status_code == 404
