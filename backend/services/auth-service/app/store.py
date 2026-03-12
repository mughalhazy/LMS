from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Optional

from .models import ResetChallenge, Session, Tenant, UserCredential
from .security import hash_password


class InMemoryAuthStore:
    def __init__(self) -> None:
        self.tenants: Dict[str, Tenant] = {
            "tenant-acme": Tenant(tenant_id="tenant-acme", name="Acme Corp"),
            "tenant-globex": Tenant(tenant_id="tenant-globex", name="Globex Inc"),
        }
        self.users_by_email: Dict[tuple[str, str], UserCredential] = {}
        self.sessions: Dict[str, Session] = {}
        self.reset_challenges_by_token: Dict[str, ResetChallenge] = {}
        self._seed()

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

    def save_session(self, user_id: str, tenant_id: str, access_ttl_s: int, refresh_ttl_s: int) -> Session:
        now = datetime.now(timezone.utc)
        session = Session(
            session_id=secrets.token_urlsafe(24),
            user_id=user_id,
            tenant_id=tenant_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=access_ttl_s),
            refresh_expires_at=now + timedelta(seconds=refresh_ttl_s),
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
        challenge = ResetChallenge(
            challenge_id=secrets.token_urlsafe(12),
            user_id=user_id,
            tenant_id=tenant_id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )
        self.reset_challenges_by_token[challenge.token] = challenge
        return challenge

    def get_reset_challenge(self, token: str) -> Optional[ResetChallenge]:
        return self.reset_challenges_by_token.get(token)

    def update_password(self, tenant_id: str, email: str, new_password_hash: str) -> bool:
        user = self.get_user_by_email(tenant_id, email)
        if user is None:
            return False
        user.password_hash = new_password_hash
        return True
