from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class OfflineProgressRecord:
    offline_progress_id: str
    student_id: str
    tenant_id: str
    content_id: str
    lesson_id: str
    playback_position: int
    completion_percent: float
    local_timestamp: datetime
    sync_status: str
    reference_token: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "OfflineProgressRecord":
        normalized_timestamp = self.local_timestamp
        if normalized_timestamp.tzinfo is None:
            normalized_timestamp = normalized_timestamp.replace(tzinfo=timezone.utc)
        else:
            normalized_timestamp = normalized_timestamp.astimezone(timezone.utc)
        return OfflineProgressRecord(
            offline_progress_id=self.offline_progress_id.strip() or str(uuid4()),
            student_id=self.student_id.strip(),
            tenant_id=self.tenant_id.strip(),
            content_id=self.content_id.strip(),
            lesson_id=self.lesson_id.strip(),
            playback_position=max(0, int(self.playback_position)),
            completion_percent=max(0.0, min(100.0, float(self.completion_percent))),
            local_timestamp=normalized_timestamp,
            sync_status=self.sync_status.strip() or "queued",
            reference_token=self.reference_token.strip(),
            metadata={str(key).strip(): value for key, value in self.metadata.items() if str(key).strip()},
        )
