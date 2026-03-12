from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}."


def test_provider_registration_and_activation_flow():
    registration = client.post(
        "/provider/tools/register",
        json={
            "tenant_id": "tenant_a",
            "tool_name": "Acme Tool",
            "initiate_login_uri": "https://tool.example.com/login",
            "redirect_uris": ["https://tool.example.com/launch"],
            "jwks_uri": "https://tool.example.com/jwks",
            "requested_scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
            ],
            "deployment_context": "course",
            "default_role_mapping": {"Instructor": "instructor"},
            "admin_actor_id": "admin_1",
        },
    )
    assert registration.status_code == 200
    tool_id = registration.json()["tool_id"]

    activation = client.post(
        "/provider/tools/validate-activation",
        json={
            "tool_id": tool_id,
            "jwks_fetch_result": True,
            "redirect_uri_verification_result": True,
            "scope_policy_check": True,
            "tenant_security_policy": "strict",
            "admin_approval": True,
        },
    )
    assert activation.status_code == 200
    assert activation.json()["activation_decision"] is True


def test_consumer_launch_flow():
    register = client.post(
        "/consumer/tools/register",
        json={
            "tenant_id": "tenant_a",
            "tool_name": "Video Lab",
            "issuer": "https://lms.example.com",
            "client_id": "client_abc",
            "deployment_id": "dep_abc",
            "launch_url": "https://tool.example.com/launch",
            "jwks_endpoint": "https://tool.example.com/jwks",
            "oidc_auth_initiation_url": "https://tool.example.com/oidc/init",
            "target_link_uri": "https://tool.example.com/launch",
            "allowed_message_types": ["LtiResourceLinkRequest"],
        },
    )
    assert register.status_code == 200
    tool_id = register.json()["tool_id"]

    initiated = client.post(
        "/consumer/launch/initiate",
        json={
            "tool_id": tool_id,
            "user_id": "u-1",
            "course_id": "course-1",
            "resource_link_id": "res-1",
            "role": "Learner",
            "locale": "en-US",
            "custom_params": {"chapter": "intro"},
        },
    )
    assert initiated.status_code == 200
    state = initiated.json()["state"]
    nonce = initiated.json()["nonce"]

    token = _jwt(
        {
            "sub": "u-1",
            "email": "u1@example.com",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "dep_abc",
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        }
    )
    complete = client.post(
        "/consumer/launch/complete",
        json={"tool_id": tool_id, "id_token": token, "state": state, "nonce": nonce},
    )
    assert complete.status_code == 200
    assert complete.json()["launch_status"] == "launched"
