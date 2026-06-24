from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Optional

from .models import ResetChallenge, Session, Tenant, UserCredential
from .security import hash_password


class InMemoryAuthStore:
    def __init__(self) -> None:
        self.tenants: Dict[str, Tenant] = {
            "tenant-acme": Tenant(tenant_id="tenant-acme", name="Acme Corp", domain="acme.test"),
            "tenant-globex": Tenant(tenant_id="tenant-globex", name="Globex Inc", domain="globex.test"),
        }
        self.users_by_email: Dict[tuple[str, str], UserCredential] = {}
        self.sessions: Dict[str, Session] = {}
        self.reset_challenges_by_token: Dict[str, ResetChallenge] = {}
        self._failed_attempts: dict[tuple[str, str], int] = {}
        self._lockout_until: dict[tuple[str, str], datetime] = {}
        self._revoked_jtis: set[str] = set()
        # AUD-050: token family tracking — spec §3 refresh_token_family entity.
        # Maps jti → family_id so that replay of any token in a family revokes all siblings.
        self._jti_to_family: Dict[str, str] = {}
        self._revoked_families: set[str] = set()
        self._seed()

    def record_failed_attempt(self, tenant_id: str, user_id: str) -> int:
        key = (tenant_id, user_id)
        count = self._failed_attempts.get(key, 0) + 1
        self._failed_attempts[key] = count
        if count >= 5:
            self._lockout_until[key] = datetime.now(timezone.utc) + timedelta(minutes=15)
        return count

    def clear_failed_attempts(self, tenant_id: str, user_id: str) -> None:
        key = (tenant_id, user_id)
        self._failed_attempts.pop(key, None)
        self._lockout_until.pop(key, None)

    def is_locked(self, tenant_id: str, user_id: str) -> bool:
        key = (tenant_id, user_id)
        lockout = self._lockout_until.get(key)
        if lockout is None:
            return False
        if datetime.now(timezone.utc) >= lockout:
            self._lockout_until.pop(key, None)
            self._failed_attempts.pop(key, None)
            return False
        return True

    def revoke_jti(self, jti: str) -> None:
        self._revoked_jtis.add(jti)
        # AUD-050: if jti belongs to a family, revoke the entire family
        family_id = self._jti_to_family.get(jti)
        if family_id:
            self._revoked_families.add(family_id)

    def is_jti_revoked(self, jti: str) -> bool:
        if jti in self._revoked_jtis:
            return True
        # AUD-050: jti is revoked if its family was revoked (replay detection)
        family_id = self._jti_to_family.get(jti)
        return family_id is not None and family_id in self._revoked_families

    def register_token_family(self, jti: str, family_id: str) -> None:
        """AUD-050: associate a refresh token jti with a family for replay revocation."""
        self._jti_to_family[jti] = family_id

    def is_family_revoked(self, family_id: str) -> bool:
        return family_id in self._revoked_families

    def _seed(self) -> None:
        seeded = [
            UserCredential(
                user_id="user-1",
                tenant_id="tenant-acme",
                organization_id="org-acme-1",
                email="admin@acme.test",
                password_hash=hash_password("AcmePass#123"),
                roles=["Tenant Admin"],
            ),
            UserCredential(
                user_id="user-2",
                tenant_id="tenant-globex",
                organization_id="org-globex-1",
                email="learner@globex.test",
                password_hash=hash_password("GlobexPass#123"),
                roles=["Learner"],
            ),
        ]

        for user in seeded:
            self.users_by_email[(user.tenant_id, user.email.lower())] = user

    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[UserCredential]:
        return self.users_by_email.get((tenant_id, email.lower()))

    def get_user_by_id(self, tenant_id: str, user_id: str) -> Optional[UserCredential]:
        for user in self.users_by_email.values():
            if user.tenant_id == tenant_id and user.user_id == user_id:
                return user
        return None

    def update_password_by_user_id(self, tenant_id: str, user_id: str, new_password_hash: str) -> bool:
        user = self.get_user_by_id(tenant_id, user_id)
        if user is None:
            return False
        user.password_hash = new_password_hash
        return True

    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        domain_lower = domain.lower().lstrip("@")
        for tenant in self.tenants.values():
            if tenant.domain and tenant.domain.lower() == domain_lower:
                return tenant
        return None

    def save_session(self, user_id: str, tenant_id: str, access_ttl_s: int, refresh_ttl_s: int,
                     auth_method: str = "password", assurance_level: str = "password") -> Session:
        now = datetime.now(timezone.utc)
        session = Session(
            session_id=secrets.token_urlsafe(24),
            user_id=user_id,
            tenant_id=tenant_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=access_ttl_s),
            refresh_expires_at=now + timedelta(seconds=refresh_ttl_s),
            last_seen_at=now,
            # CAT-012: auth_method and assurance_level from storage contract
            auth_method=auth_method,
            assurance_level=assurance_level,
        )
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def revoke_session(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session:
            session.revoked = True

    def create_reset_challenge(self, user_id: str, tenant_id: str, ttl_seconds: int = 900) -> ResetChallenge:
        import hashlib as _hl
        plain_token = secrets.token_urlsafe(32)
        # CAT-013: store hash, never plain token — plain is given to client only
        token_hash = _hl.sha256(plain_token.encode()).hexdigest()
        challenge = ResetChallenge(
            challenge_id=secrets.token_urlsafe(12),
            user_id=user_id,
            tenant_id=tenant_id,
            token=plain_token,         # returned to caller once; not stored plain
            challenge_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )
        # Index by hash so lookup never requires plain token in store
        self.reset_challenges_by_token[token_hash] = challenge
        return challenge

    def get_reset_challenge(self, token: str) -> Optional[ResetChallenge]:
        import hashlib as _hl
        # CAT-013: accept both hash (new) and plain (legacy callers) for backward compat
        by_hash = self.reset_challenges_by_token.get(_hl.sha256(token.encode()).hexdigest())
        if by_hash:
            return by_hash
        return self.reset_challenges_by_token.get(token)

    def update_password(self, tenant_id: str, email: str, new_password_hash: str) -> bool:
        user = self.get_user_by_email(tenant_id, email)
        if user is None:
            return False
        user.password_hash = new_password_hash
        return True
