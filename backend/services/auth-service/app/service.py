from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Tuple

from .schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenValidationRequest,
)
from .audit import AuditLogger
from .security import hash_password, issue_token, validate_token, verify_password
from .store import InMemoryAuthStore


class AuthService:
    def __init__(self, store: InMemoryAuthStore, signing_secret: str, audit_logger: AuditLogger | None = None) -> None:
        self.store = store
        self.signing_secret = signing_secret
        self.audit_logger = audit_logger or AuditLogger("auth.audit")
        self.access_ttl_s = 900
        self.refresh_ttl_s = 7 * 24 * 3600

    def login(self, req: LoginRequest) -> Tuple[int, Dict[str, object]]:
        tenant = self.store.tenants.get(req.tenant_id)
        if tenant is None or not tenant.active:
            self.audit_logger.log(
                event_type="authentication.login.denied",
                tenant_id=req.tenant_id,
                actor_id=req.email,
                details={"reason": "tenant_not_available"},
            )
            return 403, {"error": "tenant_not_available"}

        user = self.store.get_user_by_email(req.tenant_id, req.email)
        if user is None:
            self.audit_logger.log(
                event_type="authentication.login.denied",
                tenant_id=req.tenant_id,
                actor_id=req.email,
                details={"reason": "invalid_credentials"},
            )
            return 401, {"error": "invalid_credentials"}

        if user.status != "active":
            self.audit_logger.log(
                event_type="authentication.login.denied",
                tenant_id=req.tenant_id,
                actor_id=user.user_id,
                details={"reason": "account_disabled"},
            )
            return 403, {"error": "account_disabled"}

        if not verify_password(req.password, user.password_hash):
            self.audit_logger.log(
                event_type="authentication.login.denied",
                tenant_id=req.tenant_id,
                actor_id=user.user_id,
                details={"reason": "invalid_credentials"},
            )
            return 401, {"error": "invalid_credentials"}

        user.last_login_at = datetime.now(timezone.utc)
        session = self.store.save_session(user.user_id, user.tenant_id, self.access_ttl_s, self.refresh_ttl_s)
        self.audit_logger.log(
            event_type="authentication.login.succeeded",
            tenant_id=req.tenant_id,
            actor_id=user.user_id,
            details={"session_id": session.session_id, "roles": user.roles},
        )

        return 200, {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "session_id": session.session_id,
            "roles": user.roles,
            "token_exchange_required": True,
        }

    def issue_tokens(self, req: TokenRequest) -> Tuple[int, Dict[str, object]]:
        session = self.store.get_session(req.session_id)
        if session is None or session.revoked:
            return 401, {"error": "invalid_session"}

        if session.tenant_id != req.tenant_id or session.user_id != req.user_id:
            return 403, {"error": "tenant_context_mismatch"}

        claims = {
            "sub": req.user_id,
            "tenant_id": req.tenant_id,
            "session_id": req.session_id,
            "roles": req.roles,
            "scope": "lms.api",
        }

        access_token = issue_token(self.signing_secret, claims, self.access_ttl_s)
        refresh_claims = {**claims, "token_type": "refresh"}
        refresh_token = issue_token(self.signing_secret, refresh_claims, self.refresh_ttl_s)

        return 200, {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_ttl_s,
            "refresh_token": refresh_token,
            "refresh_expires_in": self.refresh_ttl_s,
        }

    def validate_session(self, req: TokenValidationRequest) -> Tuple[int, Dict[str, object]]:
        valid, payload, error = validate_token(self.signing_secret, req.access_token)
        if not valid or payload is None:
            return 401, {"active": False, "error": error}

        if payload.get("tenant_id") != req.tenant_id:
            return 403, {"active": False, "error": "tenant_context_mismatch"}

        session_id = payload.get("session_id")
        session = self.store.get_session(str(session_id)) if session_id else None
        if session is None or session.revoked:
            return 401, {"active": False, "error": "session_not_active"}

        return 200, {
            "active": True,
            "tenant_id": payload.get("tenant_id"),
            "user_id": payload.get("sub"),
            "roles": payload.get("roles", []),
            "expires_at": payload.get("exp"),
        }

    def forgot_password(self, req: ForgotPasswordRequest) -> Tuple[int, Dict[str, object]]:
        tenant = self.store.tenants.get(req.tenant_id)
        if tenant is None or not tenant.active:
            return 403, {"error": "tenant_not_available"}

        user = self.store.get_user_by_email(req.tenant_id, req.email)
        if user is None:
            return 202, {"status": "accepted"}

        challenge = self.store.create_reset_challenge(user.user_id, req.tenant_id)
        return 202, {
            "status": "accepted",
            "challenge_id": challenge.challenge_id,
            "reset_token": challenge.token,
            "expires_at": int(challenge.expires_at.timestamp()),
        }

    def reset_password(self, req: ResetPasswordRequest) -> Tuple[int, Dict[str, object]]:
        challenge = self.store.get_reset_challenge(req.reset_token)
        if challenge is None:
            return 400, {"error": "invalid_reset_token"}

        if challenge.used:
            return 400, {"error": "token_already_used"}

        now = datetime.now(timezone.utc)
        if challenge.expires_at < now:
            return 400, {"error": "token_expired"}

        if challenge.tenant_id != req.tenant_id:
            return 403, {"error": "tenant_context_mismatch"}

        updated = self.store.update_password(req.tenant_id, req.email, hash_password(req.new_password))
        if not updated:
            return 404, {"error": "user_not_found"}

        challenge.used = True
        return 200, {"status": "password_reset"}
