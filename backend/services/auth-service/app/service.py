from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from .schemas import (
    AdminResetPasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenValidationRequest,
)
from .audit import AuditLogger
from .security import hash_password, issue_token, validate_token, verify_password
from .store import InMemoryAuthStore

logger = logging.getLogger("auth-service")


def _bus_publish(event_type: str, tenant_id: str, payload: Dict[str, Any], correlation_id: str = "") -> None:
    """AUD-031: publish auth events to platform bus. Best-effort â€” never blocks auth flow."""
    try:
        import sys
        _root = Path(__file__).resolve().parents[4]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
        publish_event(
            event_type=event_type,
            topic=event_type,
            producer_service="auth-service",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            payload=payload,
        )
    except Exception as exc:
        logger.warning("auth-service: failed to publish event %s to bus: %s", event_type, exc)


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
                event_type="auth.login.failed",
                tenant_id=req.tenant_id,
                actor_id=req.email,
                details={"reason": "tenant_not_available"},
            )
            return 401, {"error": "tenant_not_available"}

        identifier = getattr(req, "identifier", None) or getattr(req, "email", "")
        user = self.store.get_user_by_email(req.tenant_id, identifier)
        if user is None:
            self.audit_logger.log(
                event_type="auth.login.failed",
                tenant_id=req.tenant_id,
                actor_id=identifier,
                details={"reason": "invalid_credentials"},
            )
            _bus_publish("auth.login.failed", req.tenant_id, {"reason": "invalid_credentials"})
            return 401, {"error": "invalid_credentials"}

        # G-19: lockout check (after user resolved, before status check)
        if hasattr(self.store, "is_locked") and self.store.is_locked(req.tenant_id, user.user_id):
            _bus_publish("auth.account.locked", req.tenant_id, {"user_id": user.user_id, "reason_code": "failed_attempts"})
            return 423, {"error": "account_locked", "retry_after": 900}

        if user.status != "active":
            self.audit_logger.log(
                event_type="auth.login.failed",
                tenant_id=req.tenant_id,
                actor_id=user.user_id,
                details={"reason": "account_disabled"},
            )
            _bus_publish("auth.login.failed", req.tenant_id, {"user_id": user.user_id, "reason": "account_disabled"})
            return 401, {"error": "account_disabled"}

        if not verify_password(req.password, user.password_hash):
            # G-19: track failed attempts
            if hasattr(self.store, "record_failed_attempt"):
                self.store.record_failed_attempt(req.tenant_id, user.user_id)
            self.audit_logger.log(
                event_type="auth.login.failed",
                tenant_id=req.tenant_id,
                actor_id=user.user_id,
                details={"reason": "invalid_credentials"},
            )
            _bus_publish("auth.login.failed", req.tenant_id, {"user_id": user.user_id, "reason": "invalid_credentials"})
            return 401, {"error": "invalid_credentials"}

        # G-19: clear failed attempts on success
        if hasattr(self.store, "clear_failed_attempts"):
            self.store.clear_failed_attempts(req.tenant_id, user.user_id)

        user.last_login_at = datetime.now(timezone.utc)
        session = self.store.save_session(user.user_id, user.tenant_id, self.access_ttl_s, self.refresh_ttl_s)

        # G-18: one-step login â€” issue tokens directly (spec Â§4.1)
        claims = {
            "sub": user.user_id,
            "tenant_id": user.tenant_id,
            "session_id": session.session_id,
            "roles": user.roles,
            "scope": "lms.api",
        }
        access_token = issue_token(self.signing_secret, claims, self.access_ttl_s)
        import uuid as _uuid
        initial_family_id = str(_uuid.uuid4())
        initial_jti = str(_uuid.uuid4())
        # AUD-050: seed token family on login; family_id tracks refresh token lineage for replay detection
        refresh_claims = {**claims, "token_type": "refresh", "family_id": initial_family_id, "jti": initial_jti}
        refresh_token = issue_token(self.signing_secret, refresh_claims, self.refresh_ttl_s)
        if hasattr(self.store, "register_token_family"):
            self.store.register_token_family(initial_jti, initial_family_id)

        self.audit_logger.log(
            event_type="auth.login.succeeded.v1",
            tenant_id=req.tenant_id,
            actor_id=user.user_id,
            details={"session_id": session.session_id, "roles": user.roles},
        )
        # AUD-031 + CAT-008: publish to platform bus with full integration-doc payload
        client = getattr(req, "client", None)
        _bus_publish("auth.login.succeeded", req.tenant_id, {
            "user_id": user.user_id,
            "session_id": session.session_id,
            "auth_method": "password",
            "assurance_level": "password",
            "client_id": getattr(client, "device_id", "") if client else "",
            "ip": getattr(client, "ip", "") if client else "",
        })

        return 200, {
            "session_id": session.session_id,
            "user": {"user_id": user.user_id, "tenant_id": user.tenant_id},
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_ttl_s,
            "refresh_token": refresh_token,
            "refresh_expires_in": self.refresh_ttl_s,
        }

    def refresh_token(self, req: "RefreshTokenRequest") -> Tuple[int, Dict[str, object]]:  # noqa: F821
        """AUD-052/002: spec Â§4.2 â€” proper refresh token validation and rotation."""
        from .schemas import RefreshTokenRequest as _RTR  # noqa: F401
        valid, payload, error = validate_token(
            self.signing_secret,
            req.refresh_token,
            is_jti_revoked=getattr(self.store, "is_jti_revoked", None),
        )
        if not valid or payload is None:
            return 401, {"error": error or "invalid_refresh_token"}
        if payload.get("token_type") != "refresh":
            return 401, {"error": "not_a_refresh_token"}
        if payload.get("tenant_id") != req.tenant_id:
            return 401, {"error": "tenant_context_mismatch"}
        session_id = str(payload.get("session_id", ""))
        session = self.store.get_session(session_id) if session_id else None
        if session is None or session.revoked:
            return 401, {"error": "session_not_active"}
        # AUD-050: revoke old jti; if this is a replay (family already revoked), reject
        old_jti = str(payload.get("jti", ""))
        old_family = payload.get("family_id", old_jti)  # family_id carried in refresh token claims
        if old_jti and hasattr(self.store, "is_family_revoked") and self.store.is_family_revoked(str(old_family)):
            return 409, {"error": "token_family_revoked", "detail": "Refresh token replay detected â€” all sessions in this family have been revoked."}
        if old_jti and hasattr(self.store, "revoke_jti"):
            self.store.revoke_jti(old_jti)
        claims = {
            "sub": str(payload.get("sub", "")),
            "tenant_id": req.tenant_id,
            "session_id": session_id,
            "roles": payload.get("roles", []),
            "scope": payload.get("scope", "lms.api"),
        }
        access_token = issue_token(self.signing_secret, claims, self.access_ttl_s)
        import uuid as _uuid
        new_jti = str(_uuid.uuid4())
        refresh_claims = {**claims, "token_type": "refresh", "family_id": str(old_family), "jti": new_jti}
        new_refresh_token = issue_token(self.signing_secret, refresh_claims, self.refresh_ttl_s)
        # Register new jti in the same token family
        if hasattr(self.store, "register_token_family"):
            self.store.register_token_family(new_jti, str(old_family))
        _bus_publish("auth.token.refreshed", req.tenant_id, {"session_id": session_id, "user_id": claims["sub"]})
        return 200, {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_ttl_s,
            "refresh_token": new_refresh_token,
            "refresh_expires_in": self.refresh_ttl_s,
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
        _is_jti_revoked = getattr(self.store, "is_jti_revoked", None)
        valid, payload, error = validate_token(self.signing_secret, req.access_token, is_jti_revoked=_is_jti_revoked)
        if not valid or payload is None:
            return 401, {"active": False, "error": error}

        if payload.get("tenant_id") != req.tenant_id:
            # AUD-046: spec Â§4.5 documents only 401 for validate failures
            return 401, {"active": False, "error": "tenant_context_mismatch"}

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
            "session_id": payload.get("session_id"),
            "scopes": [s.strip() for s in str(payload.get("scope", "")).split() if s.strip()],
        }

    def forgot_password(self, req: ForgotPasswordRequest) -> Tuple[int, Dict[str, object]]:
        tenant = self.store.tenants.get(req.tenant_id)
        if tenant is None or not tenant.active:
            # AUD-025: anti-enumeration â€” return 202 regardless of tenant existence
            return 202, {"status": "accepted"}

        identifier = getattr(req, "identifier", None) or getattr(req, "email", "")
        user = self.store.get_user_by_email(req.tenant_id, identifier)
        if user is None:
            # AUD-025: anti-enumeration â€” always 202, never reveal user/tenant existence
            _bus_publish("auth.password.reset.requested", req.tenant_id, {})
            return 202, {"status": "accepted"}

        self.store.create_reset_challenge(user.user_id, req.tenant_id)
        _bus_publish("auth.password.reset.requested", req.tenant_id, {"user_id": user.user_id})
        # Anti-enumeration: always return generic 202 â€” reset token delivered out-of-band.
        return 202, {"status": "accepted"}

    def reset_password(self, req: ResetPasswordRequest) -> Tuple[int, Dict[str, object]]:
        token = getattr(req, "challenge_token", None) or getattr(req, "reset_token", "")
        challenge = self.store.get_reset_challenge(token)
        if challenge is None:
            return 400, {"error": "invalid_reset_token"}

        if challenge.used:
            return 400, {"error": "token_already_used"}

        now = datetime.now(timezone.utc)
        if challenge.expires_at < now:
            return 400, {"error": "token_expired"}

        if challenge.tenant_id != req.tenant_id:
            return 401, {"error": "tenant_context_mismatch"}

        identifier = getattr(req, "email", "") or getattr(req, "identifier", "")
        updated = self.store.update_password(req.tenant_id, identifier, hash_password(req.new_password))
        if not updated:
            return 404, {"error": "user_not_found"}

        challenge.used = True
        # AUD-026: revoke all active sessions on password reset
        user_id = challenge.user_id if hasattr(challenge, "user_id") else ""
        if user_id and hasattr(self.store, "sessions"):
            for session in self.store.sessions.values():
                if session.tenant_id == req.tenant_id and getattr(session, "user_id", None) == user_id:
                    session.revoked = True
        _bus_publish("auth.password.reset.completed", req.tenant_id, {"user_id": user_id, "global_logout": True})
        # AUD-016: spec response uses password_updated + global_logout
        return 200, {"status": "password_updated", "global_logout": True}

    def logout(self, req: LoginRequest) -> Tuple[int, Dict[str, object]]:
        """Spec Â§4.3 â€” revoke a single session."""
        session_id = getattr(req, "session_id", None) or ""
        tenant_id = getattr(req, "tenant_id", "") or ""
        session = self.store.get_session(session_id) if session_id else None
        if session is None or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        session.revoked = True
        self.audit_logger.log(
            event_type="auth.session.revoked",
            tenant_id=tenant_id,
            actor_id=session.user_id,
            details={"session_id": session_id, "reason": "user_logout"},
        )
        _bus_publish("auth.session.revoked", tenant_id, {"session_id": session_id, "user_id": session.user_id, "reason_code": "user_logout"})
        return 204, {}

    def logout_all(self, req: LoginRequest) -> Tuple[int, Dict[str, object]]:
        """Spec Â§4.4 â€” revoke all sessions for a user."""
        tenant_id = getattr(req, "tenant_id", "") or ""
        user_id = getattr(req, "user_id", "") or ""
        revoked = 0
        for session in self.store.sessions.values() if hasattr(self.store, "sessions") else []:
            if session.tenant_id == tenant_id and session.user_id == user_id and not session.revoked:
                session.revoked = True
                revoked += 1
        self.audit_logger.log(
            event_type="auth.session.logout_all.v1",
            tenant_id=tenant_id,
            actor_id=user_id,
            details={"sessions_revoked": revoked},
        )
        _bus_publish("auth.session.revoked", tenant_id, {"user_id": user_id, "reason_code": "logout_all", "sessions_revoked": revoked})
        return 202, {"status": "accepted", "sessions_revoked": revoked}

    def admin_reset_password(self, user_id: str, req: AdminResetPasswordRequest) -> Tuple[int, Dict[str, object]]:
        # Spec: auth-service-spec.md Â§2.1 â€” admin credential operations; Â§8 tenant context required
        tenant = self.store.tenants.get(req.tenant_id)
        if tenant is None or not tenant.active:
            return 403, {"error": "tenant_not_available"}

        updated = self.store.update_password_by_user_id(req.tenant_id, user_id, hash_password(req.new_password))
        if not updated:
            return 404, {"error": "user_not_found"}

        self.audit_logger.log(
            event_type="auth.admin.password_reset.v1",
            tenant_id=req.tenant_id,
            actor_id=req.actor_id,
            details={"target_user_id": user_id},
        )
        return 200, {"status": "password_reset", "user_id": user_id}

    def discover_tenant(self, domain: str) -> Tuple[int, Dict[str, object]]:
        # Spec: auth-service-spec.md Â§8 â€” tenant context; enables pre-login tenant resolution by email domain
        tenant = self.store.get_tenant_by_domain(domain) if hasattr(self.store, "get_tenant_by_domain") else None
        if tenant is None:
            return 404, {"error": "tenant_not_found"}
        return 200, {"tenant_id": tenant.tenant_id, "name": tenant.name, "domain": tenant.domain}

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
            self.audit_logger.log(event_type="auth.sso.no_provider", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type})
            return 404, {"error": "sso_provider_not_configured"}

        corr_id = (correlation_id or str(uuid4())).strip()
        try:
            redirect_url = sso_provider.initiate(redirect_uri=redirect_uri, correlation_id=corr_id)
        except Exception as exc:
            self.audit_logger.log(event_type="auth.sso.initiate_failed", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "error": str(exc)})
            return 500, {"error": "sso_initiate_failed"}

        self.audit_logger.log(event_type="auth.sso.initiated", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "correlation_id": corr_id})
        return 200, {"redirect_url": redirect_url, "correlation_id": corr_id, "provider_type": provider_type}

    def sso_callback(
        self,
        *,
        tenant_id: str,
        provider_type: str,
        code_or_assertion: str,
        correlation_id: str,
    ) -> Tuple[int, Dict[str, object]]:
        """CGAP-054: process SSO callback â€” exchange code/assertion for identity claims,
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
            self.audit_logger.log(event_type="auth.sso.callback_failed", tenant_id=tenant_id, actor_id="system", details={"provider_type": provider_type, "correlation_id": correlation_id})
            return 401, {"error": "sso_assertion_invalid"}

        user_id = str(claims.get("user_id") or claims.get("sub") or "").strip()
        email = str(claims.get("email") or "").strip()
        roles = [str(r) for r in claims.get("roles", []) if str(r).strip()]
        if not user_id:
            return 401, {"error": "sso_identity_unresolvable"}

        # Create or refresh the platform session for the federated identity
        session = self.store.save_session(user_id, tenant_id, self.access_ttl_s, self.refresh_ttl_s)
        self.audit_logger.log(
            event_type="auth.sso.login.succeeded",
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
    """Factory â€” prefers SQLiteAuthStore when db_path is given, falls back to InMemoryAuthStore."""
    if db_path is not None:
        from .store_db import SQLiteAuthStore  # lazy import keeps in-memory path dependency-free
        store: Any = SQLiteAuthStore(db_path=db_path, tenant_id="__auth__")
    else:
        store = InMemoryAuthStore()
    return AuthService(store=store, signing_secret=signing_secret, audit_logger=audit_logger)
