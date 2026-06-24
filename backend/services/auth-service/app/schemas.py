from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClientContext:
    """AUD-012: spec §4.1 client object — captures device/IP for audit trail."""
    client_type: str = "web"
    device_id: str = ""
    ip: str = ""
    user_agent: str = ""


@dataclass
class LoginRequest:
    tenant_id: str
    password: str
    # AUD-012: spec uses 'identifier' (email/username/phone); 'email' kept as alias
    identifier: str = ""
    email: str = ""  # backward-compat alias; service prefers identifier
    client: Optional[ClientContext] = None

    def __post_init__(self) -> None:
        # Prefer identifier; fall back to email for legacy callers
        if not self.identifier and self.email:
            self.identifier = self.email
        elif self.identifier and not self.email:
            self.email = self.identifier


@dataclass
class TokenRequest:
    tenant_id: str
    user_id: str
    session_id: str
    roles: List[str]


@dataclass
class RefreshTokenRequest:
    """AUD-052: spec §4.2 refresh token request."""
    tenant_id: str
    refresh_token: str


@dataclass
class TokenValidationRequest:
    tenant_id: str
    access_token: str


@dataclass
class ForgotPasswordRequest:
    tenant_id: str
    # AUD-013: spec uses 'identifier'; 'email' kept as alias
    identifier: str = ""
    email: str = ""  # backward-compat alias
    channel: str = "email"  # AUD-013: delivery channel

    def __post_init__(self) -> None:
        if not self.identifier and self.email:
            self.identifier = self.email
        elif self.identifier and not self.email:
            self.email = self.identifier


@dataclass
class ResetPasswordRequest:
    tenant_id: str
    new_password: str
    # AUD-014: spec uses 'challenge_token'; 'reset_token' kept as alias
    challenge_token: str = ""
    reset_token: str = ""  # backward-compat alias
    email: str = ""  # kept for legacy callers; not required by spec

    def __post_init__(self) -> None:
        if not self.challenge_token and self.reset_token:
            self.challenge_token = self.reset_token
        elif self.challenge_token and not self.reset_token:
            self.reset_token = self.challenge_token


@dataclass
class AdminResetPasswordRequest:
    tenant_id: str
    new_password: str
    actor_id: str


def to_json_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return dict(obj)
