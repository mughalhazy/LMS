from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Tenant:
    tenant_id: str
    name: str
    active: bool = True
    domain: str | None = None


@dataclass
class UserCredential:
    user_id: str
    tenant_id: str
    organization_id: str
    email: str
    password_hash: str
    roles: List[str] = field(default_factory=list)
    status: str = "active"
    last_login_at: datetime | None = None


@dataclass
class Session:
    session_id: str
    user_id: str
    tenant_id: str
    issued_at: datetime
    expires_at: datetime
    refresh_expires_at: datetime
    revoked: bool = False
    # CAT-012: auth-service-storage-contract fields
    auth_method: str = "password"
    assurance_level: str = "password"
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None

    @property
    def state(self) -> str:
        """CAT-012: canonical state enum per storage contract (active|revoked|expired)."""
        from datetime import timezone
        if self.revoked:
            return "revoked"
        if datetime.now(timezone.utc) > self.expires_at:
            return "expired"
        return "active"


@dataclass
class ResetChallenge:
    challenge_id: str
    user_id: str
    tenant_id: str
    token: str          # plain token given to client
    expires_at: datetime
    used: bool = False
    # CAT-013: auth-service-storage-contract fields
    challenge_hash: str = ""       # hashed version stored for verification
    delivery_channel: str = "email"
    attempt_count: int = 0
    max_attempts: int = 5


@dataclass
class LoginResponse:
    session_id: str
    access_token: str
    refresh_token: str
    user_id: str
    tenant_id: str
    roles: List[str]
    expires_in: int       # seconds until access_token expiry
    token_type: str = "Bearer"
