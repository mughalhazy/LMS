from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class MediaAccessPolicy:
    media_id: str
    tenant_id: str
    user_id: str
    capability_id: str
    token_expiry: datetime
    watermark_payload: dict[str, Any] = field(default_factory=dict)
    allowed_device_count: int = 1
    allowed_session_count: int = 1
    offline_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "MediaAccessPolicy":
        expiry = self.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        return MediaAccessPolicy(
            media_id=self.media_id.strip(),
            tenant_id=self.tenant_id.strip(),
            user_id=self.user_id.strip(),
            capability_id=self.capability_id.strip(),
            token_expiry=expiry.astimezone(timezone.utc),
            watermark_payload=dict(self.watermark_payload),
            allowed_device_count=max(int(self.allowed_device_count), 0),
            allowed_session_count=max(int(self.allowed_session_count), 0),
            offline_allowed=bool(self.offline_allowed),
            metadata=dict(self.metadata),
        )


__all__ = ["MediaAccessPolicy"]
