import base64
import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

os.environ["JWT_SHARED_SECRET"] = "test-secret"

from app.main import app, publisher  # noqa: E402

client = TestClient(app)


def _jwt(tenant_id: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_raw = {"sub": "tester", "tenant_id": tenant_id, "exp": int(time.time()) + 3600}
    payload = base64.urlsafe_b64encode(json.dumps(payload_raw).encode()).decode().rstrip("=")
    signed = f"{header}.{payload}".encode()
    sig = base64.urlsafe_b64encode(hmac.new(b"test-secret", signed, hashlib.sha256).digest()).decode().rstrip("=")
    return f"{header}.{payload}.{sig}"


def _headers(tenant_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_jwt(tenant_id)}",
        "X-Tenant-Id": tenant_id,
    }


def test_versioned_role_assignment_and_authorize_allow():
    role = client.post(
        "/api/v1/rbac/roles",
        json={"role_key": "tenant-admin", "display_name": "Tenant Admin", "description": "admin"},
        headers=_headers("t-1"),
    )
    assert role.status_code == 201
    role_id = role.json()["role_id"]

    bind = client.put(
        f"/api/v1/rbac/roles/{role_id}/permissions",
        json={"permissions": ["tenant.settings.manage", "audit.view_tenant"]},
        headers=_headers("t-1"),
    )
    assert bind.status_code == 204

    create = client.post(
        "/api/v1/rbac/assignments",
        json={
            "subject_type": "user",
            "subject_id": "u-1",
            "role_id": role_id,
            "scope_type": "tenant",
            "scope_id": "t-1",
            "source": "direct",
            "created_by": "admin-user",
        },
        headers=_headers("t-1"),
    )
    assert create.status_code == 201

    decision = client.post(
        "/api/v1/rbac/authorize",
        json={
            "subject": {"type": "user", "id": "u-1"},
            "permission_key": "tenant.settings.manage",
            "resource": {"type": "tenant", "id": "t-1"},
            "scope_type": "tenant",
            "scope_id": "t-1",
            "context": {},
        },
        headers=_headers("t-1"),
    )
    assert decision.status_code == 200
    assert decision.json()["decision"] == "allow"


def test_tenant_isolation_blocks_cross_tenant_read():
    role = client.post(
        "/api/v1/rbac/roles",
        json={"role_key": "reader", "display_name": "Reader", "description": "reader"},
        headers=_headers("tenant-a"),
    )
    assert role.status_code == 201

    tenant_b_roles = client.get("/api/v1/rbac/roles", headers=_headers("tenant-b"))
    assert tenant_b_roles.status_code == 200
    assert tenant_b_roles.json() == []


def test_explicit_deny_policy_overrides_allow_and_events_published():
    role = client.post(
        "/api/v1/rbac/roles",
        json={"role_key": "publisher", "display_name": "Publisher", "description": "publisher"},
        headers=_headers("t-2"),
    )
    role_id = role.json()["role_id"]

    client.put(
        f"/api/v1/rbac/roles/{role_id}/permissions",
        json={"permissions": ["course.publish"]},
        headers=_headers("t-2"),
    )
    client.post(
        "/api/v1/rbac/assignments",
        json={
            "subject_type": "user",
            "subject_id": "u-deny",
            "role_id": role_id,
            "scope_type": "tenant",
            "scope_id": "t-2",
            "source": "direct",
            "created_by": "admin-user",
        },
        headers=_headers("t-2"),
    )
    client.post(
        "/api/v1/rbac/policy-rules",
        json={"rule_type": "explicit_deny", "expression": {"permission_key": "course.publish"}, "priority": 1},
        headers=_headers("t-2"),
    )
    decision = client.post(
        "/api/v1/rbac/authorize",
        json={
            "subject": {"type": "user", "id": "u-deny"},
            "permission_key": "course.publish",
            "resource": {"type": "course", "id": "c1"},
            "scope_type": "tenant",
            "scope_id": "t-2",
            "context": {},
        },
        headers=_headers("t-2"),
    )
    assert decision.json()["decision"] == "deny"
    assert "explicit_deny_rule" in decision.json()["reason_codes"]
    assert any(evt["event_type"] == "rbac.policy_rule.changed.v1" for evt in publisher.published)
