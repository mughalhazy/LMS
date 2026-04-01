from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ExamSessionStatus = Literal["scheduled", "active", "submitted", "expired", "cancelled"]


@dataclass(frozen=True)
class TenantCapacityProfile:
    max_active_sessions: int = 5_000
    shard_count: int = 8
    burst_queue_limit: int = 0
    allow_concurrent_sessions_per_student: bool = False


@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    timestamp: datetime
    tenant_id: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QueuedExamSession:
    exam_session_id: str
    shard_id: int
    queued_at: datetime


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


@dataclass
class TenantPartition:
    profile: TenantCapacityProfile
    next_session_number: int = 1
    next_audit_sequence: int = 1
    sessions: dict[str, ExamSession] = field(default_factory=dict)
    active_sessions: dict[str, ExamSession] = field(default_factory=dict)
    student_active_index: dict[str, set[str]] = field(default_factory=dict)
    shard_active_sessions: dict[int, set[str]] = field(default_factory=dict)
    shard_queues: dict[int, list[QueuedExamSession]] = field(default_factory=dict)
    audit_log: list[AuditRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.shard_active_sessions = {sid: set() for sid in range(self.profile.shard_count)}
        self.shard_queues = {sid: [] for sid in range(self.profile.shard_count)}
