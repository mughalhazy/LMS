from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


class LearningIntegration(Protocol):
    def publish_exam_session_event(self, event: dict[str, Any]) -> None: ...


class AnalyticsIntegration(Protocol):
    def publish_exam_analytics_event(self, event: dict[str, Any]) -> None: ...


@dataclass
class InMemoryLearningIntegration:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish_exam_session_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)


@dataclass
class InMemoryAnalyticsIntegration:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish_exam_analytics_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)


@dataclass(frozen=True)
class TenantCapacityProfile:
    max_active_sessions: int = 5_000
    shard_count: int = 8


@dataclass
class ExamSession:
    session_id: str
    tenant_id: str
    learner_id: str
    exam_id: str
    status: str
    started_at: datetime
    submitted_at: datetime | None = None
    score: float | None = None


@dataclass
class _TenantPartition:
    profile: TenantCapacityProfile
    active_sessions: dict[str, ExamSession] = field(default_factory=dict)
    completed_sessions: dict[str, ExamSession] = field(default_factory=dict)
    shards: dict[int, set[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.shards = {shard_id: set() for shard_id in range(self.profile.shard_count)}


class ExamEngineService:
    """High-concurrency, tenant-isolated exam session engine.

    Design goals:
    - Load handling through tenant-local capacity and shard partitioning.
    - Hard tenant isolation for active/completed sessions.
    - Dedicated learning + analytics integration hooks.
    - No shared global session queue bottleneck.
    """

    def __init__(
        self,
        *,
        learning_integration: LearningIntegration | None = None,
        analytics_integration: AnalyticsIntegration | None = None,
    ) -> None:
        self._learning = learning_integration or InMemoryLearningIntegration()
        self._analytics = analytics_integration or InMemoryAnalyticsIntegration()
        self._tenant_partitions: dict[str, _TenantPartition] = {}
        self._next_session_number = 1

    def register_tenant(self, tenant_id: str, profile: TenantCapacityProfile | None = None) -> None:
        if tenant_id not in self._tenant_partitions:
            self._tenant_partitions[tenant_id] = _TenantPartition(profile=profile or TenantCapacityProfile())

    def _partition_for(self, tenant_id: str) -> _TenantPartition:
        if tenant_id not in self._tenant_partitions:
            self.register_tenant(tenant_id)
        return self._tenant_partitions[tenant_id]

    def _next_session_id(self, tenant_id: str) -> str:
        session_number = self._next_session_number
        self._next_session_number += 1
        return f"{tenant_id}-exam-session-{session_number}"

    def _shard_for_session(self, *, tenant_id: str, session_id: str) -> int:
        shard_count = self._partition_for(tenant_id).profile.shard_count
        return abs(hash((tenant_id, session_id))) % shard_count

    def start_session(self, *, tenant_id: str, learner_id: str, exam_id: str) -> ExamSession:
        partition = self._partition_for(tenant_id)
        if len(partition.active_sessions) >= partition.profile.max_active_sessions:
            raise RuntimeError("TENANT_EXAM_CAPACITY_REACHED")

        session_id = self._next_session_id(tenant_id)
        started_at = datetime.now(timezone.utc)
        session = ExamSession(
            session_id=session_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            exam_id=exam_id,
            status="active",
            started_at=started_at,
        )

        partition.active_sessions[session_id] = session
        shard = self._shard_for_session(tenant_id=tenant_id, session_id=session_id)
        partition.shards[shard].add(session_id)
        return session

    def submit_session(self, *, tenant_id: str, session_id: str, score: float) -> ExamSession:
        partition = self._partition_for(tenant_id)
        session = partition.active_sessions.get(session_id)
        if session is None:
            raise KeyError("SESSION_NOT_FOUND")

        session.status = "submitted"
        session.score = score
        session.submitted_at = datetime.now(timezone.utc)

        partition.completed_sessions[session_id] = session
        del partition.active_sessions[session_id]

        event_envelope = {
            "tenant_id": tenant_id,
            "event_type": "exam.session.submitted",
            "session_id": session.session_id,
            "learner_id": session.learner_id,
            "exam_id": session.exam_id,
            "score": session.score,
            "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
        }
        self._learning.publish_exam_session_event(event_envelope)
        self._analytics.publish_exam_analytics_event(event_envelope)
        return session

    def tenant_metrics(self, tenant_id: str) -> dict[str, Any]:
        partition = self._partition_for(tenant_id)
        return {
            "tenant_id": tenant_id,
            "active_sessions": len(partition.active_sessions),
            "completed_sessions": len(partition.completed_sessions),
            "shard_load": {
                shard_id: len(partition.shards[shard_id])
                for shard_id in sorted(partition.shards)
            },
        }
