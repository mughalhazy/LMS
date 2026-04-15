from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class LoginRequest:
    tenant_id: str
    email: str
    password: str


@dataclass
class TokenRequest:
    tenant_id: str
    user_id: str
    session_id: str
    roles: List[str]


@dataclass
class TokenValidationRequest:
    tenant_id: str
    access_token: str


@dataclass
class ForgotPasswordRequest:
    tenant_id: str
    email: str


@dataclass
class ResetPasswordRequest:
    tenant_id: str
    email: str
    reset_token: str
    new_password: str


def to_json_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return dict(obj)
