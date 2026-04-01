from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

_MODELS_PATH = Path(__file__).resolve().with_name("models.py")
_spec = importlib.util.spec_from_file_location("exam_engine_models", _MODELS_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load exam engine models")
_models = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _models
_spec.loader.exec_module(_models)

ExamSession = _models.ExamSession
TenantCapacityProfile = _models.TenantCapacityProfile


class LearningIntegration(Protocol):
    def publish_exam_session_event(self, event: dict[str, Any]) -> None: ...


class AnalyticsIntegration(Protocol):
    def publish_exam_analytics_event(self, event: dict[str, Any]) -> None: ...


class AssessmentAttemptIntegration(Protocol):
    def ensure_attempt(
        self,
        *,
        tenant_id: str,
        exam_id: str,
        student_id: str,
        requested_attempt_id: str | None,
    ) -> str: ...


class ProgressIntegration(Protocol):
    def publish_progress_update(self, event: dict[str, Any]) -> None: ...


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


@dataclass
class InMemoryAssessmentAttemptIntegration:
    attempts: dict[tuple[str, str], str] = field(default_factory=dict)

    def ensure_attempt(
        self,
        *,
        tenant_id: str,
        exam_id: str,
        student_id: str,
        requested_attempt_id: str | None,
    ) -> str:
        if requested_attempt_id:
            self.attempts[(tenant_id, requested_attempt_id)] = exam_id
            return requested_attempt_id
        attempt_number = len([1 for (t, _), _v in self.attempts.items() if t == tenant_id]) + 1
        attempt_id = f"{tenant_id}-attempt-{attempt_number}"
        self.attempts[(tenant_id, attempt_id)] = exam_id
        return attempt_id


@dataclass
class InMemoryProgressIntegration:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish_progress_update(self, event: dict[str, Any]) -> None:
        self.events.append(event)


@dataclass
class _AuditRecord:
    sequence: int
    timestamp: datetime
    tenant_id: str
    action: str
    details: dict[str, Any]


@dataclass
class _QueuedExamSession:
    exam_session_id: str
    queued_at: datetime


@dataclass
class _TenantPartition:
    profile: TenantCapacityProfile
    next_session_number: int = 1
    sessions: dict[str, ExamSession] = field(default_factory=dict)
    active_sessions: dict[str, ExamSession] = field(default_factory=dict)
    student_active_index: dict[str, set[str]] = field(default_factory=dict)
    shard_active_sessions: dict[int, set[str]] = field(default_factory=dict)
    shard_queues: dict[int, list[_QueuedExamSession]] = field(default_factory=dict)
    audit_log: list[_AuditRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.shard_active_sessions = {sid: set() for sid in range(self.profile.shard_count)}
        self.shard_queues = {sid: [] for sid in range(self.profile.shard_count)}


class ExamEngineService:
    def __init__(
        self,
        *,
        learning_integration: LearningIntegration | None = None,
        analytics_integration: AnalyticsIntegration | None = None,
        assessment_attempt_integration: AssessmentAttemptIntegration | None = None,
        progress_integration: ProgressIntegration | None = None,
    ) -> None:
        self._learning = learning_integration or InMemoryLearningIntegration()
        self._analytics = analytics_integration or InMemoryAnalyticsIntegration()
        self._attempts = assessment_attempt_integration or InMemoryAssessmentAttemptIntegration()
        self._progress = progress_integration or InMemoryProgressIntegration()
        self._tenant_partitions: dict[str, _TenantPartition] = {}

    def register_tenant(self, tenant_id: str, profile: TenantCapacityProfile | None = None) -> None:
        if tenant_id not in self._tenant_partitions:
            self._tenant_partitions[tenant_id] = _TenantPartition(profile=profile or TenantCapacityProfile())

    def _partition_for(self, tenant_id: str) -> _TenantPartition:
        if tenant_id not in self._tenant_partitions:
            self.register_tenant(tenant_id)
        return self._tenant_partitions[tenant_id]

    def _record_audit(self, *, partition: _TenantPartition, tenant_id: str, action: str, details: dict[str, Any]) -> None:
        partition.audit_log.append(
            _AuditRecord(
                sequence=len(partition.audit_log) + 1,
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                action=action,
                details=details,
            )
        )

    def _next_session_id(self, tenant_id: str) -> str:
        partition = self._partition_for(tenant_id)
        session_id = f"{tenant_id}-exam-session-{partition.next_session_number}"
        partition.next_session_number += 1
        return session_id

    def _stable_shard(self, *, tenant_id: str, learner_id: str, exam_id: str) -> int:
        shard_count = self._partition_for(tenant_id).profile.shard_count
        digest = hashlib.sha256(f"{tenant_id}:{learner_id}:{exam_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % shard_count

    def _publish(self, payload: dict[str, Any]) -> None:
        self._learning.publish_exam_session_event(payload)
        self._analytics.publish_exam_analytics_event(payload)

    def _get_session(self, *, tenant_id: str, exam_session_id: str) -> tuple[_TenantPartition, ExamSession]:
        partition = self._partition_for(tenant_id)
        session = partition.sessions.get(exam_session_id)
        if session is None:
            raise KeyError("SESSION_NOT_FOUND")
        if session.tenant_id != tenant_id:
            raise PermissionError("TENANT_ISOLATION_VIOLATION")
        return partition, session

    def _assert_student_concurrency(self, partition: _TenantPartition, student_id: str) -> None:
        if partition.profile.allow_concurrent_sessions_per_student:
            return
        if partition.student_active_index.get(student_id):
            raise RuntimeError("CONFLICTING_ACTIVE_SESSION")

    def create_exam_session(
        self,
        *,
        tenant_id: str,
        exam_id: str,
        student_id: str,
        attempt_id: str | None = None,
        expires_at: datetime | None = None,
        assigned_capacity_profile: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> ExamSession:
        partition = self._partition_for(tenant_id)
        self._assert_student_concurrency(partition, student_id)
        resolved_attempt_id = self._attempts.ensure_attempt(
            tenant_id=tenant_id,
            exam_id=exam_id,
            student_id=student_id,
            requested_attempt_id=attempt_id,
        )
        now = datetime.now(timezone.utc)
        session = ExamSession(
            exam_session_id=self._next_session_id(tenant_id),
            tenant_id=tenant_id,
            exam_id=exam_id,
            student_id=student_id,
            attempt_id=resolved_attempt_id,
            status="scheduled",
            started_at=None,
            expires_at=expires_at or (now + timedelta(hours=2)),
            submitted_at=None,
            assigned_capacity_profile=assigned_capacity_profile,
            isolation_key=f"{tenant_id}:{student_id}:{exam_id}",
            assigned_shard=self._stable_shard(tenant_id=tenant_id, learner_id=student_id, exam_id=exam_id),
            metadata=metadata or {},
        )
        partition.sessions[session.exam_session_id] = session
        self._record_audit(
            partition=partition,
            tenant_id=tenant_id,
            action="exam.session.created",
            details={"exam_session_id": session.exam_session_id, "student_id": student_id},
        )
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.created", "exam_session_id": session.exam_session_id})
        return session

    def start_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status not in {"scheduled", "queued", "active"}:
            raise RuntimeError("SESSION_NOT_STARTABLE")
        if session.status == "active":
            return session

        if len(partition.active_sessions) >= partition.profile.max_active_sessions:
            shard = session.assigned_shard if session.assigned_shard is not None else 0
            queue = partition.shard_queues[shard]
            if len(queue) >= partition.profile.burst_queue_limit:
                raise RuntimeError("TENANT_EXAM_CAPACITY_REACHED")
            session.status = "queued"
            queue.append(_QueuedExamSession(exam_session_id=session.exam_session_id, queued_at=datetime.now(timezone.utc)))
            self._record_audit(
                partition=partition,
                tenant_id=tenant_id,
                action="exam.session.queued",
                details={"exam_session_id": session.exam_session_id, "shard": shard},
            )
            return session

        session.status = "active"
        session.started_at = datetime.now(timezone.utc)
        partition.active_sessions[session.exam_session_id] = session
        partition.student_active_index.setdefault(session.student_id, set()).add(session.exam_session_id)
        partition.shard_active_sessions[session.assigned_shard or 0].add(session.exam_session_id)
        self._record_audit(
            partition=partition,
            tenant_id=tenant_id,
            action="exam.session.started",
            details={"exam_session_id": session.exam_session_id, "shard": session.assigned_shard},
        )
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.started", "exam_session_id": session.exam_session_id})
        return session

    def heartbeat_exam_session(self, *, tenant_id: str, exam_session_id: str, expires_at: datetime | None = None) -> ExamSession:
        _partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status != "active":
            raise RuntimeError("SESSION_NOT_ACTIVE")
        if session.expires_at and datetime.now(timezone.utc) > session.expires_at:
            return self.expire_exam_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if expires_at is not None:
            session.expires_at = expires_at
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.heartbeat", "exam_session_id": session.exam_session_id})
        return session

    def _drain_next_queued(self, partition: _TenantPartition) -> None:
        if len(partition.active_sessions) >= partition.profile.max_active_sessions:
            return
        for shard_id in sorted(partition.shard_queues):
            queue = partition.shard_queues[shard_id]
            if not queue:
                continue
            queued = queue.pop(0)
            session = partition.sessions.get(queued.exam_session_id)
            if session is None or session.status != "queued":
                continue
            session.status = "active"
            session.started_at = datetime.now(timezone.utc)
            partition.active_sessions[session.exam_session_id] = session
            partition.student_active_index.setdefault(session.student_id, set()).add(session.exam_session_id)
            partition.shard_active_sessions[shard_id].add(session.exam_session_id)
            break

    def submit_exam_session(self, *, tenant_id: str, exam_session_id: str, score: float) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status != "active":
            raise RuntimeError("SESSION_NOT_ACTIVE")
        session.status = "submitted"
        session.submitted_at = datetime.now(timezone.utc)
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions[session.assigned_shard or 0].discard(exam_session_id)
        self._drain_next_queued(partition)
        self._record_audit(
            partition=partition,
            tenant_id=tenant_id,
            action="exam.session.submitted",
            details={"exam_session_id": session.exam_session_id, "score": score},
        )
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.submitted", "exam_session_id": session.exam_session_id, "score": score, "assigned_shard": session.assigned_shard})
        self._progress.publish_progress_update({"tenant_id": tenant_id, "event_type": "progress.exam.completed", "student_id": session.student_id, "exam_id": session.exam_id, "attempt_id": session.attempt_id, "score": score})
        return session

    def expire_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status in {"submitted", "cancelled", "expired"}:
            return session
        session.status = "expired"
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions[session.assigned_shard or 0].discard(exam_session_id)
        self._drain_next_queued(partition)
        return session

    def cancel_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status == "submitted":
            raise RuntimeError("SESSION_ALREADY_SUBMITTED")
        session.status = "cancelled"
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions[session.assigned_shard or 0].discard(exam_session_id)
        self._drain_next_queued(partition)
        return session

    def start_session(self, *, tenant_id: str, learner_id: str, exam_id: str) -> ExamSession:
        created = self.create_exam_session(tenant_id=tenant_id, exam_id=exam_id, student_id=learner_id)
        return self.start_exam_session(tenant_id=tenant_id, exam_session_id=created.exam_session_id)

    def submit_session(self, *, tenant_id: str, session_id: str, score: float) -> ExamSession:
        return self.submit_exam_session(tenant_id=tenant_id, exam_session_id=session_id, score=score)

    def tenant_metrics(self, tenant_id: str) -> dict[str, Any]:
        partition = self._partition_for(tenant_id)
        status_counts = {"scheduled": 0, "queued": 0, "active": 0, "submitted": 0, "expired": 0, "cancelled": 0}
        for session in partition.sessions.values():
            status_counts[session.status] += 1
        return {
            "tenant_id": tenant_id,
            "active_sessions": len(partition.active_sessions),
            "completed_sessions": status_counts["submitted"],
            "status_counts": status_counts,
            "shard_load": {shard_id: len(partition.shard_active_sessions[shard_id]) for shard_id in sorted(partition.shard_active_sessions)},
            "queue_depth": {shard_id: len(partition.shard_queues[shard_id]) for shard_id in sorted(partition.shard_queues)},
        }

    def tenant_audit_log(self, tenant_id: str) -> list[dict[str, Any]]:
        partition = self._partition_for(tenant_id)
        return [
            {
                "sequence": rec.sequence,
                "timestamp": rec.timestamp.isoformat(),
                "tenant_id": rec.tenant_id,
                "action": rec.action,
                "details": dict(rec.details),
            }
            for rec in partition.audit_log
        ]
