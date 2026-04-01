from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SyncConflictType(str, Enum):
    DUPLICATE_PROGRESS_UPDATE = "duplicate_progress_update"
    STALE_STATE_OVERWRITE = "stale_state_overwrite"
    SIMULTANEOUS_ONLINE_OFFLINE_UPDATE = "simultaneous_online_offline_update"
    INVALID_OR_EXPIRED_OFFLINE_PACKAGE = "invalid_or_expired_offline_package"


@dataclass
class OfflineProgressEnvelope:
    operation_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    lesson_id: str
    enrollment_id: str
    completion_status: str
    score: float | None
    time_spent_seconds: int
    attempt_count: int
    timestamp: str
    package_expires_at: str | None = None
    sync_attempts: int = 0
    last_error: str | None = None

    @property
    def dedupe_key(self) -> str:
        parts = [
            self.tenant_id,
            self.learner_id,
            self.course_id,
            self.lesson_id,
            self.enrollment_id,
            self.completion_status,
            str(self.score),
            str(self.time_spent_seconds),
            str(self.attempt_count),
            self.timestamp,
        ]
        return "|".join(parts)


@dataclass
class SyncConflict:
    conflict_type: SyncConflictType
    strategy: str
    reason: str


__all__ = ["OfflineProgressEnvelope", "SyncConflict", "SyncConflictType"]
