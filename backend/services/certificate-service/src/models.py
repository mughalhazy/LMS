from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ExpirationPolicy:
    validity_days: Optional[int] = None
    never_expires: bool = False


@dataclass
class Certificate:
    certificate_id: str
    verification_code: str
    tenant_id: str
    user_id: str
    course_id: str
    enrollment_id: Optional[str]
    issued_at: datetime
    expires_at: Optional[datetime]
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifact_uri: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
