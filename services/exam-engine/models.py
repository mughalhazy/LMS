from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TenantCapacityProfile:
    max_active_sessions: int = 5_000
    shard_count: int = 8
    burst_queue_limit: int = 1_000


@dataclass
class ExamSession:
    session_id: str
    tenant_id: str
    learner_id: str
    exam_id: str
    status: str
    started_at: datetime
    assigned_shard: int
    submitted_at: datetime | None = None
    score: float | None = None
    queued_at: datetime | None = None


@dataclass
class QueuedExamSession:
    session_id: str
    tenant_id: str
    learner_id: str
    exam_id: str
    queued_at: datetime
    assigned_shard: int


@dataclass
class AuditRecord:
    sequence: int
    timestamp: datetime
    tenant_id: str
    action: str
    details: dict[str, str | int | float | None]


@dataclass
class TenantPartition:
    profile: TenantCapacityProfile
    active_sessions: dict[str, ExamSession] = field(default_factory=dict)
    completed_sessions: dict[str, ExamSession] = field(default_factory=dict)
    queued_sessions: dict[str, QueuedExamSession] = field(default_factory=dict)
    shard_active_sessions: dict[int, set[str]] = field(default_factory=dict)
    shard_queues: dict[int, deque[str]] = field(default_factory=dict)
    audit_log: list[AuditRecord] = field(default_factory=list)
    next_session_number: int = 1

    def __post_init__(self) -> None:
        self.shard_active_sessions = {
            shard_id: set() for shard_id in range(self.profile.shard_count)
        }
        self.shard_queues = {
            shard_id: deque() for shard_id in range(self.profile.shard_count)
        }
