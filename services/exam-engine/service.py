from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

try:
    from models import AuditRecord, ExamSession, QueuedExamSession, TenantCapacityProfile, TenantPartition
except ModuleNotFoundError:
    _models_path = Path(__file__).with_name("models.py")
    _models_spec = importlib.util.spec_from_file_location("exam_engine_models", _models_path)
    if _models_spec is None or _models_spec.loader is None:
        raise RuntimeError("Unable to load exam engine models module")
    _models_module = importlib.util.module_from_spec(_models_spec)
    sys.modules[_models_spec.name] = _models_module
    _models_spec.loader.exec_module(_models_module)
    AuditRecord = _models_module.AuditRecord
    ExamSession = _models_module.ExamSession
    QueuedExamSession = _models_module.QueuedExamSession
    TenantCapacityProfile = _models_module.TenantCapacityProfile
    TenantPartition = _models_module.TenantPartition


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


class ExamEngineService:
    """High-concurrency, tenant-isolated exam session engine."""

    def __init__(
        self,
        *,
        learning_integration: LearningIntegration | None = None,
        analytics_integration: AnalyticsIntegration | None = None,
    ) -> None:
        self._learning = learning_integration or InMemoryLearningIntegration()
        self._analytics = analytics_integration or InMemoryAnalyticsIntegration()
        self._tenant_partitions: dict[str, TenantPartition] = {}
        self._audit_sequence = 1

    def register_tenant(self, tenant_id: str, profile: TenantCapacityProfile | None = None) -> None:
        if tenant_id not in self._tenant_partitions:
            self._tenant_partitions[tenant_id] = TenantPartition(profile=profile or TenantCapacityProfile())

    def _partition_for(self, tenant_id: str) -> TenantPartition:
        if tenant_id not in self._tenant_partitions:
            self.register_tenant(tenant_id)
        return self._tenant_partitions[tenant_id]

    def _next_session_id(self, tenant_id: str) -> str:
        partition = self._partition_for(tenant_id)
        session_number = partition.next_session_number
        partition.next_session_number += 1
        return f"{tenant_id}-exam-session-{session_number}"

    def _stable_shard(self, *, tenant_id: str, learner_id: str, exam_id: str) -> int:
        shard_count = self._partition_for(tenant_id).profile.shard_count
        digest = hashlib.sha256(f"{tenant_id}:{learner_id}:{exam_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % shard_count

    def _record_audit(self, tenant_id: str, action: str, details: dict[str, str | int | float | None]) -> None:
        partition = self._partition_for(tenant_id)
        partition.audit_log.append(
            AuditRecord(
                sequence=self._audit_sequence,
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                action=action,
                details=details,
            )
        )
        self._audit_sequence += 1

    def evaluate_exam_capacity(self, *, tenant_id: str) -> dict[str, Any]:
        partition = self._partition_for(tenant_id)
        active = len(partition.active_sessions)
        queued = len(partition.queued_sessions)
        profile = partition.profile

        if active < profile.max_active_sessions:
            decision = "admit"
            reason = "runtime_capacity_available"
        elif queued < profile.burst_queue_limit:
            decision = "defer"
            reason = "runtime_saturated_queued_for_burst"
        else:
            decision = "reject"
            reason = "runtime_and_queue_capacity_exceeded"

        return {
            "tenant_id": tenant_id,
            "decision": decision,
            "reason": reason,
            "active_sessions": active,
            "queued_sessions": queued,
            "max_active_sessions": profile.max_active_sessions,
            "burst_queue_limit": profile.burst_queue_limit,
        }

    def allocate_exam_runtime_slot(self, *, tenant_id: str, learner_id: str, exam_id: str) -> ExamSession:
        capacity = self.evaluate_exam_capacity(tenant_id=tenant_id)
        if capacity["decision"] != "admit":
            raise RuntimeError(f"CANNOT_ALLOCATE_RUNTIME_SLOT:{capacity['decision']}")

        session_id = self._next_session_id(tenant_id)
        shard = self._stable_shard(tenant_id=tenant_id, learner_id=learner_id, exam_id=exam_id)
        started_at = datetime.now(timezone.utc)
        session = ExamSession(
            session_id=session_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            exam_id=exam_id,
            status="active",
            started_at=started_at,
            assigned_shard=shard,
        )
        partition = self._partition_for(tenant_id)
        partition.active_sessions[session_id] = session
        partition.shard_active_sessions[shard].add(session_id)
        self._record_audit(
            tenant_id,
            "runtime_slot_allocated",
            {"session_id": session_id, "learner_id": learner_id, "exam_id": exam_id, "assigned_shard": shard},
        )
        return session

    def queue_exam_session(self, *, tenant_id: str, learner_id: str, exam_id: str) -> QueuedExamSession:
        partition = self._partition_for(tenant_id)
        if len(partition.queued_sessions) >= partition.profile.burst_queue_limit:
            raise RuntimeError("TENANT_BURST_QUEUE_CAPACITY_REACHED")

        session_id = self._next_session_id(tenant_id)
        shard = self._stable_shard(tenant_id=tenant_id, learner_id=learner_id, exam_id=exam_id)
        queued = QueuedExamSession(
            session_id=session_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            exam_id=exam_id,
            queued_at=datetime.now(timezone.utc),
            assigned_shard=shard,
        )
        partition.queued_sessions[session_id] = queued
        partition.shard_queues[shard].append(session_id)
        self._record_audit(
            tenant_id,
            "session_deferred_to_queue",
            {"session_id": session_id, "learner_id": learner_id, "exam_id": exam_id, "assigned_shard": shard},
        )
        return queued

    def release_exam_runtime_slot(self, *, tenant_id: str, session_id: str) -> ExamSession | None:
        partition = self._partition_for(tenant_id)
        session = partition.active_sessions.get(session_id)
        if session is None:
            return None

        del partition.active_sessions[session_id]
        partition.shard_active_sessions[session.assigned_shard].discard(session_id)
        self._record_audit(tenant_id, "runtime_slot_released", {"session_id": session_id})

        shard_queue = partition.shard_queues[session.assigned_shard]
        while shard_queue and len(partition.active_sessions) < partition.profile.max_active_sessions:
            queued_session_id = shard_queue.popleft()
            queued = partition.queued_sessions.pop(queued_session_id, None)
            if queued is None:
                continue
            promoted = ExamSession(
                session_id=queued.session_id,
                tenant_id=queued.tenant_id,
                learner_id=queued.learner_id,
                exam_id=queued.exam_id,
                status="active",
                started_at=datetime.now(timezone.utc),
                assigned_shard=queued.assigned_shard,
                queued_at=queued.queued_at,
            )
            partition.active_sessions[promoted.session_id] = promoted
            partition.shard_active_sessions[promoted.assigned_shard].add(promoted.session_id)
            self._record_audit(
                tenant_id,
                "queued_session_promoted",
                {"session_id": promoted.session_id, "assigned_shard": promoted.assigned_shard},
            )
            break

        return session

    def start_session(self, *, tenant_id: str, learner_id: str, exam_id: str) -> ExamSession:
        capacity = self.evaluate_exam_capacity(tenant_id=tenant_id)
        if capacity["decision"] == "admit":
            return self.allocate_exam_runtime_slot(tenant_id=tenant_id, learner_id=learner_id, exam_id=exam_id)
        if capacity["decision"] == "defer":
            queued = self.queue_exam_session(tenant_id=tenant_id, learner_id=learner_id, exam_id=exam_id)
            raise RuntimeError(f"TENANT_EXAM_CAPACITY_DEFERRED:{queued.session_id}")

        self._record_audit(
            tenant_id,
            "session_rejected",
            {
                "learner_id": learner_id,
                "exam_id": exam_id,
                "reason": str(capacity["reason"]),
            },
        )
        raise RuntimeError("TENANT_EXAM_CAPACITY_REACHED")

    def submit_session(self, *, tenant_id: str, session_id: str, score: float) -> ExamSession:
        partition = self._partition_for(tenant_id)
        session = partition.active_sessions.get(session_id)
        if session is None:
            raise KeyError("SESSION_NOT_FOUND")

        session.status = "submitted"
        session.score = score
        session.submitted_at = datetime.now(timezone.utc)

        partition.completed_sessions[session_id] = session
        self.release_exam_runtime_slot(tenant_id=tenant_id, session_id=session_id)

        event_envelope = {
            "tenant_id": tenant_id,
            "event_type": "exam.session.submitted",
            "session_id": session.session_id,
            "learner_id": session.learner_id,
            "exam_id": session.exam_id,
            "score": session.score,
            "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
            "assigned_shard": session.assigned_shard,
        }
        self._learning.publish_exam_session_event(event_envelope)
        self._analytics.publish_exam_analytics_event(event_envelope)
        self._record_audit(
            tenant_id,
            "session_submitted",
            {"session_id": session_id, "score": score, "assigned_shard": session.assigned_shard},
        )
        return session

    def tenant_metrics(self, tenant_id: str) -> dict[str, Any]:
        partition = self._partition_for(tenant_id)
        return {
            "tenant_id": tenant_id,
            "active_sessions": len(partition.active_sessions),
            "queued_sessions": len(partition.queued_sessions),
            "completed_sessions": len(partition.completed_sessions),
            "shard_load": {
                shard_id: len(partition.shard_active_sessions[shard_id])
                for shard_id in sorted(partition.shard_active_sessions)
            },
            "queue_depth": {
                shard_id: len(partition.shard_queues[shard_id])
                for shard_id in sorted(partition.shard_queues)
            },
        }

    def tenant_audit_log(self, tenant_id: str) -> list[dict[str, Any]]:
        partition = self._partition_for(tenant_id)
        return [
            {
                "sequence": record.sequence,
                "timestamp": record.timestamp.isoformat(),
                "tenant_id": record.tenant_id,
                "action": record.action,
                "details": dict(record.details),
            }
            for record in partition.audit_log
        ]
