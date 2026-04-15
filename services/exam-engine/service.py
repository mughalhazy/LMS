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

AuditRecord = _models.AuditRecord
ExamSession = _models.ExamSession
QueuedExamSession = _models.QueuedExamSession
TenantCapacityProfile = _models.TenantCapacityProfile
TenantPartition = _models.TenantPartition


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


class CapabilityIntegration(Protocol):
    def is_enabled(self, *, tenant_id: str, capability_id: str) -> bool: ...


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
        idx = len([1 for (attempt_tenant, _), _ in self.attempts.items() if attempt_tenant == tenant_id]) + 1
        attempt_id = f"{tenant_id}-attempt-{idx}"
        self.attempts[(tenant_id, attempt_id)] = exam_id
        return attempt_id


@dataclass
class InMemoryProgressIntegration:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish_progress_update(self, event: dict[str, Any]) -> None:
        self.events.append(event)


@dataclass
class InMemoryCapabilityIntegration:
    enabled_capabilities: dict[str, set[str]] = field(default_factory=dict)

    def is_enabled(self, *, tenant_id: str, capability_id: str) -> bool:
        return capability_id in self.enabled_capabilities.get(tenant_id, set())


class PublishEventLearningIntegration:
    """CGAP-057: concrete LearningIntegration wired to the platform event bus."""

    def publish_exam_session_event(self, event: dict[str, Any]) -> None:
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({**event, "event_type": event.get("event_type", "exam.session.event")})
        except Exception:
            pass  # best-effort


class PublishEventAnalyticsIntegration:
    """CGAP-057: concrete AnalyticsIntegration wired to the platform event bus."""

    def publish_exam_analytics_event(self, event: dict[str, Any]) -> None:
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({**event, "event_type": event.get("event_type", "exam.analytics.event")})
        except Exception:
            pass


class PublishEventProgressIntegration:
    """CGAP-057: concrete ProgressIntegration wired to the platform event bus."""

    def publish_progress_update(self, event: dict[str, Any]) -> None:
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({**event, "event_type": event.get("event_type", "progress.updated")})
        except Exception:
            pass


class EntitlementCapabilityIntegration:
    """CGAP-057: concrete CapabilityIntegration delegating to entitlement service.

    Falls back to `True` (permissive) if entitlement service is unavailable — the exam
    engine's own capability guard will re-check at session-start time.
    """

    def __init__(self, entitlement_service: Any | None = None) -> None:
        self._entitlement = entitlement_service

    def is_enabled(self, *, tenant_id: str, capability_id: str) -> bool:
        if self._entitlement is None:
            return True  # permissive fallback when no entitlement service injected
        try:
            from shared.utils.entitlement import TenantEntitlementContext  # type: ignore[import]
            ctx = TenantEntitlementContext(tenant_id=tenant_id, plan_type="active")
            return bool(self._entitlement.is_enabled(ctx, capability_id))
        except Exception:
            return True  # best-effort fallback


def create_wired_exam_engine_integrations(
    *,
    entitlement_service: Any | None = None,
) -> dict[str, Any]:
    """CGAP-057: factory that returns concrete, platform-bus-wired integration implementations.

    Usage::

        integrations = create_wired_exam_engine_integrations(entitlement_service=my_entitlement)
        engine = ExamEngineService(**integrations)
    """
    return {
        "learning_integration": PublishEventLearningIntegration(),
        "analytics_integration": PublishEventAnalyticsIntegration(),
        "progress_integration": PublishEventProgressIntegration(),
        "capability_integration": EntitlementCapabilityIntegration(entitlement_service=entitlement_service),
        # assessment_attempt_integration left as None → caller supplies or InMemory fallback used
    }


class ExamEngineService:
    """Tenant-isolated canonical exam session state machine."""

    _CAPABILITY = "assessment.attempt"

    def __init__(
        self,
        *,
        learning_integration: LearningIntegration | None = None,
        analytics_integration: AnalyticsIntegration | None = None,
        assessment_attempt_integration: AssessmentAttemptIntegration | None = None,
        progress_integration: ProgressIntegration | None = None,
        capability_integration: CapabilityIntegration | None = None,
    ) -> None:
        self._learning = learning_integration or InMemoryLearningIntegration()
        self._analytics = analytics_integration or InMemoryAnalyticsIntegration()
        self._attempts = assessment_attempt_integration or InMemoryAssessmentAttemptIntegration()
        self._progress = progress_integration or InMemoryProgressIntegration()
        if capability_integration is None:
            raise ValueError("capability_integration is required for strict runtime capability resolution")
        self._capabilities = capability_integration
        self._tenant_partitions: dict[str, TenantPartition] = {}
        # BC-EXAM-01: per-session answer checkpoints — {exam_session_id: {question_id: answer_record}}
        # MO-025 / Phase C
        self._answer_checkpoints: dict[str, dict[str, dict[str, Any]]] = {}

    def register_tenant(self, tenant_id: str, profile: TenantCapacityProfile | None = None) -> None:
        if tenant_id not in self._tenant_partitions:
            self._tenant_partitions[tenant_id] = TenantPartition(profile=profile or TenantCapacityProfile())

    def _partition_for(self, tenant_id: str) -> TenantPartition:
        if tenant_id not in self._tenant_partitions:
            self.register_tenant(tenant_id)
        return self._tenant_partitions[tenant_id]

    def _assert_capability(self, *, tenant_id: str) -> None:
        if not self._capabilities.is_enabled(tenant_id=tenant_id, capability_id=self._CAPABILITY):
            raise PermissionError("CAPABILITY_DISABLED")

    def _next_session_id(self, tenant_id: str) -> str:
        partition = self._partition_for(tenant_id)
        session_id = f"{tenant_id}-exam-session-{partition.next_session_number}"
        partition.next_session_number += 1
        return session_id

    def _stable_shard(self, *, tenant_id: str, learner_id: str, exam_id: str) -> int:
        shard_count = self._partition_for(tenant_id).profile.shard_count
        digest = hashlib.sha256(f"{tenant_id}:{learner_id}:{exam_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % shard_count

    def _append_audit(self, *, tenant_id: str, action: str, details: dict[str, Any]) -> None:
        partition = self._partition_for(tenant_id)
        record = AuditRecord(
            sequence=partition.next_audit_sequence,
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            action=action,
            details=details,
        )
        partition.next_audit_sequence += 1
        partition.audit_log.append(record)

    def _publish(self, payload: dict[str, Any]) -> None:
        self._learning.publish_exam_session_event(payload)
        self._analytics.publish_exam_analytics_event(payload)

    def _get_session(self, *, tenant_id: str, exam_session_id: str) -> tuple[TenantPartition, ExamSession]:
        partition = self._partition_for(tenant_id)
        session = partition.sessions.get(exam_session_id)
        if session is None:
            raise KeyError("SESSION_NOT_FOUND")
        if session.tenant_id != tenant_id:
            raise PermissionError("TENANT_ISOLATION_VIOLATION")
        return partition, session

    def _assert_student_concurrency(self, partition: TenantPartition, student_id: str) -> None:
        if partition.profile.allow_concurrent_sessions_per_student:
            return
        if partition.student_active_index.get(student_id, set()):
            raise RuntimeError("CONFLICTING_ACTIVE_SESSION")

    def _try_dequeue(self, *, partition: TenantPartition, shard: int) -> None:
        while partition.shard_queues.get(shard):
            if len(partition.active_sessions) >= partition.profile.max_active_sessions:
                return
            queued = partition.shard_queues[shard].pop(0)
            session = partition.sessions.get(queued.exam_session_id)
            if session is None or session.status not in {"scheduled", "queued"}:
                continue
            self.start_exam_session(tenant_id=session.tenant_id, exam_session_id=session.exam_session_id)
            return

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
        self._assert_capability(tenant_id=tenant_id)
        partition = self._partition_for(tenant_id)
        self._assert_student_concurrency(partition, student_id)

        resolved_attempt_id = self._attempts.ensure_attempt(
            tenant_id=tenant_id,
            exam_id=exam_id,
            student_id=student_id,
            requested_attempt_id=attempt_id,
        )
        now = datetime.now(timezone.utc)
        shard = self._stable_shard(tenant_id=tenant_id, learner_id=student_id, exam_id=exam_id)
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
            assigned_shard=shard,
            metadata=dict(metadata or {}),
        )
        partition.sessions[session.exam_session_id] = session

        self._publish(
            {
                "tenant_id": tenant_id,
                "event_type": "exam.session.created",
                "exam_session_id": session.exam_session_id,
                "attempt_id": session.attempt_id,
                "student_id": student_id,
                "exam_id": exam_id,
                "status": session.status,
                "assigned_shard": shard,
            }
        )
        self._append_audit(
            tenant_id=tenant_id,
            action="exam.session.created",
            details={"exam_session_id": session.exam_session_id},
        )
        return session

    def start_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        self._assert_capability(tenant_id=tenant_id)
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status not in {"scheduled", "queued", "active"}:
            raise RuntimeError("SESSION_NOT_STARTABLE")
        if session.status == "active":
            return session

        if len(partition.active_sessions) >= partition.profile.max_active_sessions:
            queue = partition.shard_queues[session.assigned_shard or 0]
            if len(queue) >= partition.profile.burst_queue_limit:
                raise RuntimeError("TENANT_EXAM_CAPACITY_REACHED")
            session.status = "queued"
            queue.append(QueuedExamSession(exam_session_id=session.exam_session_id, shard_id=session.assigned_shard or 0, queued_at=datetime.now(timezone.utc)))
            self._append_audit(tenant_id=tenant_id, action="exam.session.queued", details={"exam_session_id": session.exam_session_id})
            return session

        session.status = "active"
        session.started_at = datetime.now(timezone.utc)
        partition.active_sessions[session.exam_session_id] = session
        partition.student_active_index.setdefault(session.student_id, set()).add(session.exam_session_id)
        partition.shard_active_sessions[session.assigned_shard or 0].add(session.exam_session_id)

        self._publish(
            {
                "tenant_id": tenant_id,
                "event_type": "exam.session.started",
                "exam_session_id": session.exam_session_id,
                "attempt_id": session.attempt_id,
                "student_id": session.student_id,
                "exam_id": session.exam_id,
                "status": session.status,
                "assigned_shard": session.assigned_shard,
            }
        )
        self._append_audit(tenant_id=tenant_id, action="exam.session.started", details={"exam_session_id": session.exam_session_id})
        return session

    def heartbeat_exam_session(self, *, tenant_id: str, exam_session_id: str, expires_at: datetime | None = None) -> ExamSession:
        _, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status != "active":
            raise RuntimeError("SESSION_NOT_ACTIVE")
        if session.expires_at and datetime.now(timezone.utc) > session.expires_at:
            return self.expire_exam_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if expires_at is not None:
            session.expires_at = expires_at
        self._publish(
            {
                "tenant_id": tenant_id,
                "event_type": "exam.session.heartbeat",
                "exam_session_id": session.exam_session_id,
                "status": session.status,
            }
        )
        self._append_audit(tenant_id=tenant_id, action="exam.session.heartbeat", details={"exam_session_id": session.exam_session_id})
        return session

    def _drain_next_queued(self, partition: TenantPartition) -> None:
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

    def submit_exam_session(self, *, tenant_id: str, exam_session_id: str, score: float, passing_score: float | None = None) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status != "active":
            raise RuntimeError("SESSION_NOT_ACTIVE")
        session.status = "submitted"
        session.submitted_at = datetime.now(timezone.utc)
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions.get(session.assigned_shard or 0, set()).discard(exam_session_id)

        self._publish(
            {
                "tenant_id": tenant_id,
                "event_type": "exam.session.submitted",
                "exam_session_id": session.exam_session_id,
                "attempt_id": session.attempt_id,
                "student_id": session.student_id,
                "exam_id": session.exam_id,
                "score": score,
                "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
                "assigned_shard": session.assigned_shard,
            }
        )
        self._progress.publish_progress_update(
            {
                "tenant_id": tenant_id,
                "event_type": "progress.exam.completed",
                "student_id": session.student_id,
                "exam_id": session.exam_id,
                "attempt_id": session.attempt_id,
                "score": score,
                "completed_at": session.submitted_at.isoformat() if session.submitted_at else None,
            }
        )
        self._append_audit(tenant_id=tenant_id, action="exam.session.submitted", details={"exam_session_id": session.exam_session_id, "score": score})

        # CGAP-056: BC-WF-01 — emit assessment.failed when score is below passing threshold.
        # Routes through existing integration protocols so the event reaches analytics,
        # learning, and any workflow engine subscriber.
        if passing_score is not None and score < passing_score:
            self._publish({
                "tenant_id": tenant_id,
                "event_type": "assessment.failed",
                "exam_session_id": session.exam_session_id,
                "attempt_id": session.attempt_id,
                "student_id": session.student_id,
                "exam_id": session.exam_id,
                "score": score,
                "passing_score": passing_score,
                "failed_at": session.submitted_at.isoformat() if session.submitted_at else None,
            })

        self._try_dequeue(partition=partition, shard=session.assigned_shard or 0)
        return session

    def expire_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status in {"submitted", "cancelled", "expired"}:
            return session
        session.status = "expired"
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions.get(session.assigned_shard or 0, set()).discard(exam_session_id)
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.expired", "exam_session_id": exam_session_id})
        self._append_audit(tenant_id=tenant_id, action="exam.session.expired", details={"exam_session_id": exam_session_id})
        self._try_dequeue(partition=partition, shard=session.assigned_shard or 0)
        return session

    def cancel_exam_session(self, *, tenant_id: str, exam_session_id: str) -> ExamSession:
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status == "submitted":
            raise RuntimeError("SESSION_ALREADY_SUBMITTED")
        session.status = "cancelled"
        partition.active_sessions.pop(exam_session_id, None)
        partition.student_active_index.get(session.student_id, set()).discard(exam_session_id)
        partition.shard_active_sessions.get(session.assigned_shard or 0, set()).discard(exam_session_id)
        self._publish({"tenant_id": tenant_id, "event_type": "exam.session.cancelled", "exam_session_id": exam_session_id})
        self._append_audit(tenant_id=tenant_id, action="exam.session.cancelled", details={"exam_session_id": exam_session_id})
        self._try_dequeue(partition=partition, shard=session.assigned_shard or 0)
        return session

    # ------------------------------------------------------------------
    # BC-EXAM-01: Answer checkpointing — MO-025 / Phase C
    # Every submitted answer is immediately persisted to _answer_checkpoints.
    # No auth or gating interrupts an active session. On reconnect,
    # resume_exam_session() restores the full checkpoint state so the
    # learner never loses progress.
    # ------------------------------------------------------------------

    def submit_answer(
        self,
        *,
        tenant_id: str,
        exam_session_id: str,
        question_id: str,
        answer: Any,
        sequence_number: int,
    ) -> dict[str, Any]:
        """Checkpoint a single answer immediately upon submission (BC-EXAM-01)."""
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status != "active":
            raise RuntimeError(f"SESSION_NOT_ACTIVE: status={session.status}")

        checkpoint_record: dict[str, Any] = {
            "question_id": question_id,
            "answer": answer,
            "sequence_number": sequence_number,
            "checkpointed_at": datetime.utcnow().isoformat(),
        }

        # Write checkpoint — tenant-isolated, session-isolated
        tenant_checkpoints = self._answer_checkpoints.setdefault(tenant_id, {})
        session_checkpoints = tenant_checkpoints.setdefault(exam_session_id, {})
        session_checkpoints[question_id] = checkpoint_record

        self._publish({
            "tenant_id": tenant_id,
            "event_type": "exam.answer.checkpointed",
            "exam_session_id": exam_session_id,
            "question_id": question_id,
            "sequence_number": sequence_number,
        })

        return {
            "exam_session_id": exam_session_id,
            "question_id": question_id,
            "checkpointed": True,
            "total_answered": len(session_checkpoints),
        }

    def get_session_answers(
        self,
        *,
        tenant_id: str,
        exam_session_id: str,
    ) -> dict[str, Any]:
        """Return all checkpointed answers for a session (used on reconnect)."""
        # Validate session exists (raises if not)
        _, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        checkpoints = (
            self._answer_checkpoints
            .get(tenant_id, {})
            .get(exam_session_id, {})
        )
        return {
            "exam_session_id": exam_session_id,
            "session_status": session.status,
            "answers": list(checkpoints.values()),
            "total_answered": len(checkpoints),
        }

    def resume_exam_session(
        self,
        *,
        tenant_id: str,
        exam_session_id: str,
    ) -> dict[str, Any]:
        """Restore full session state + checkpointed answers on reconnect (BC-EXAM-01).

        Called when a learner reconnects mid-exam. Returns the active session
        metadata plus every previously checkpointed answer so the client can
        restore exactly where the learner left off — no answers lost.
        """
        partition, session = self._get_session(tenant_id=tenant_id, exam_session_id=exam_session_id)
        if session.status not in {"active", "queued"}:
            raise RuntimeError(f"SESSION_NOT_RESUMABLE: status={session.status}")

        checkpoints = (
            self._answer_checkpoints
            .get(tenant_id, {})
            .get(exam_session_id, {})
        )

        self._publish({
            "tenant_id": tenant_id,
            "event_type": "exam.session.resumed",
            "exam_session_id": exam_session_id,
            "answers_restored": len(checkpoints),
        })
        self._append_audit(
            tenant_id=tenant_id,
            action="exam.session.resumed",
            details={"exam_session_id": exam_session_id, "answers_restored": len(checkpoints)},
        )

        return {
            "exam_session_id": exam_session_id,
            "exam_id": session.exam_id,
            "student_id": session.student_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "assigned_shard": session.assigned_shard,
            "answers": list(checkpoints.values()),
            "total_answered": len(checkpoints),
        }

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
            "shard_load": {sid: len(partition.shard_active_sessions[sid]) for sid in sorted(partition.shard_active_sessions)},
            "queue_depth": {sid: len(partition.shard_queues[sid]) for sid in sorted(partition.shard_queues)},
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
