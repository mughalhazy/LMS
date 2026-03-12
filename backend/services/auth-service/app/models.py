from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Tenant:
    tenant_id: str
    name: str
    active: bool = True


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


@dataclass
class ResetChallenge:
    challenge_id: str
    user_id: str
    tenant_id: str
    token: str
    expires_at: datetime
    used: bool = False
