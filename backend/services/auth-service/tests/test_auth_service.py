from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenValidationRequest,
)
from app.service import AuthService
from app.store import InMemoryAuthStore


def make_service() -> AuthService:
    return AuthService(InMemoryAuthStore(), signing_secret="test-secret")


def test_login_token_and_validation_success() -> None:
    service = make_service()

    status, login_payload = service.login(
        LoginRequest(
            tenant_id="tenant-acme",
            email="admin@acme.test",
            password="AcmePass#123",
        )
    )
    assert status == 200

    status, token_payload = service.issue_tokens(
        TokenRequest(
            tenant_id="tenant-acme",
            user_id=login_payload["user_id"],
            session_id=login_payload["session_id"],
            roles=login_payload["roles"],
        )
    )
    assert status == 200
    assert "access_token" in token_payload

    status, validate_payload = service.validate_session(
        TokenValidationRequest(
            tenant_id="tenant-acme",
            access_token=token_payload["access_token"],
        )
    )
    assert status == 200
    assert validate_payload["active"] is True


def test_login_rejects_cross_tenant_user() -> None:
    service = make_service()

    status, payload = service.login(
        LoginRequest(
            tenant_id="tenant-acme",
            email="learner@globex.test",
            password="GlobexPass#123",
        )
    )
    assert status == 401
    assert payload["error"] == "invalid_credentials"


def test_password_reset_flow() -> None:
    service = make_service()

    status, forgot_payload = service.forgot_password(
        ForgotPasswordRequest(tenant_id="tenant-acme", email="admin@acme.test")
    )
    assert status == 202

    status, payload = service.reset_password(
        ResetPasswordRequest(
            tenant_id="tenant-acme",
            email="admin@acme.test",
            reset_token=forgot_payload["reset_token"],
            new_password="NewAcmePass#123",
        )
    )
    assert status == 200
    assert payload["status"] == "password_reset"

    status, login_payload = service.login(
        LoginRequest(
            tenant_id="tenant-acme",
            email="admin@acme.test",
            password="NewAcmePass#123",
        )
    )
    assert status == 200
    assert login_payload["user_id"] == "user-1"
