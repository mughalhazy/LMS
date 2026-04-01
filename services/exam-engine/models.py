from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ExamSessionStatus = Literal["scheduled", "queued", "active", "submitted", "expired", "cancelled"]


@dataclass(frozen=True)
class TenantCapacityProfile:
    max_active_sessions: int = 5_000
    shard_count: int = 8
    allow_concurrent_sessions_per_student: bool = False
    burst_queue_limit: int = 0


@dataclass
class ExamSession:
    exam_session_id: str
    tenant_id: str
    exam_id: str
    student_id: str
    attempt_id: str
    status: ExamSessionStatus
    started_at: datetime | None
    expires_at: datetime | None
    submitted_at: datetime | None
    assigned_capacity_profile: str
    isolation_key: str
    assigned_shard: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def session_id(self) -> str:
        return self.exam_session_id

    @property
    def learner_id(self) -> str:
        return self.student_id
