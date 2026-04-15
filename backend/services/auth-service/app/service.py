from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

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
    def __init__(self, store: Any, signing_secret: str, audit_logger: AuditLogger | None = None) -> None:
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


    def sso_initiate(
        self,
        *,
        tenant_id: str,
        provider_type: str,
        redirect_uri: str,
        correlation_id: str | None = None,
    ) -> Tuple[int, Dict[str, object]]:
        """CGAP-054: initiate SSO flow (SAML/OIDC) and return the redirect URL.

        Delegates to an SSO provider registered on the store for this tenant.
        Returns 404 if no SSO provider is configured for the tenant.
        Returns 200 with `redirect_url` and `correlation_id` for the client to follow.
        """
        from uuid import uuid4
        sso_provider = self.store.get_sso_provider(tenant_id, provider_type) if hasattr(self.store, "get_sso_provider") else None
        if sso_provider is None:
            self.audit_logger.log(event_type="authentication.sso.no_provider", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type})
            return 404, {"error": "sso_provider_not_configured"}

        corr_id = (correlation_id or str(uuid4())).strip()
        try:
            redirect_url = sso_provider.initiate(redirect_uri=redirect_uri, correlation_id=corr_id)
        except Exception as exc:
            self.audit_logger.log(event_type="authentication.sso.initiate_failed", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "error": str(exc)})
            return 500, {"error": "sso_initiate_failed"}

        self.audit_logger.log(event_type="authentication.sso.initiated", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "correlation_id": corr_id})
        return 200, {"redirect_url": redirect_url, "correlation_id": corr_id, "provider_type": provider_type}

    def sso_callback(
        self,
        *,
        tenant_id: str,
        provider_type: str,
        code_or_assertion: str,
        correlation_id: str,
    ) -> Tuple[int, Dict[str, object]]:
        """CGAP-054: process SSO callback — exchange code/assertion for identity claims,
        then create a platform session (same session model as credential login).

        Returns 401 on invalid assertion, 404 if provider not configured.
        Returns 200 with session_id + roles for downstream token issuance.
        """
        sso_provider = self.store.get_sso_provider(tenant_id, provider_type) if hasattr(self.store, "get_sso_provider") else None
        if sso_provider is None:
            return 404, {"error": "sso_provider_not_configured"}

        try:
            claims = sso_provider.consume_callback(code_or_assertion, correlation_id)
        except Exception:
            self.audit_logger.log(event_type="authentication.sso.callback_failed", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "correlation_id": correlation_id})
            return 401, {"error": "sso_assertion_invalid"}

        user_id = str(claims.get("user_id") or claims.get("sub") or "").strip()
        email = str(claims.get("email") or "").strip()
        roles = [str(r) for r in claims.get("roles", []) if str(r).strip()]
        if not user_id:
            return 401, {"error": "sso_identity_unresolvable"}

        # Create or refresh the platform session for the federated identity
        session = self.store.save_session(user_id, tenant_id, self.access_ttl_s, self.refresh_ttl_s)
        self.audit_logger.log(
            event_type="authentication.sso.login.succeeded",
            tenant_id=tenant_id,
            actor_id=user_id,
            details={"session_id": session.session_id, "provider_type": provider_type, "email": email, "roles": roles},
        )
        return 200, {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "session_id": session.session_id,
            "roles": roles,
            "token_exchange_required": True,
        }


def create_auth_service(
    db_path: Path | None = None,
    signing_secret: str = "change-me",
    audit_logger: AuditLogger | None = None,
) -> AuthService:
    """Factory — prefers SQLiteAuthStore when db_path is given, falls back to InMemoryAuthStore."""
    if db_path is not None:
        from .store_db import SQLiteAuthStore  # lazy import keeps in-memory path dependency-free
        store: Any = SQLiteAuthStore(db_path=db_path, tenant_id="__auth__")
    else:
        store = InMemoryAuthStore()
    return AuthService(store=store, signing_secret=signing_secret, audit_logger=audit_logger)
