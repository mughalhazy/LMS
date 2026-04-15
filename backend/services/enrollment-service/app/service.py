"""Enrollment lifecycle orchestration service."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from .models import AuditLogEntry, Enrollment, EnrollmentStatus, Event, TenantContext
from .schemas import EnrollmentCreateRequest
from .store import AuditLogStore, EnrollmentStore


class NotFoundError(Exception):
    """Domain-specific exception."""


class ConflictError(Exception):
    """Domain-specific exception."""


class ValidationError(Exception):
    """Domain-specific exception."""


class EventPublisher(Protocol):
    def publish(self, event: Event) -> None: ...


class ObservabilityHook(Protocol):
    def observe(self, metric_name: str, value: float = 1.0) -> None: ...


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def publish(self, event: Event) -> None:
        self.events.append(event)


class PlatformEventBridgePublisher:
    """CGAP-055: wraps InMemoryEventPublisher and bridges key enrollment events to the platform
    event bus so that enrollment.completed drives BC-WF-01 default workflows.

    Best-effort bridge — failure never blocks enrollment lifecycle transitions.
    """

    # Events that must reach the platform bus (BC-WF-01 default workflow triggers)
    _BRIDGE_EVENT_TYPES: frozenset[str] = frozenset({
        "enrollment.lifecycle.changed",
        "enrollment.lifecycle.completed",
    })

    def __init__(self, inner: InMemoryEventPublisher | None = None) -> None:
        self.inner = inner or InMemoryEventPublisher()

    @property
    def events(self) -> list[Event]:
        return self.inner.events

    def publish(self, event: Event) -> None:
        self.inner.publish(event)
        # Bridge to platform event bus for events that drive downstream workflows
        if event.event_type in self._BRIDGE_EVENT_TYPES or (
            event.payload.get("status") == "completed"
            and event.event_type == "enrollment.lifecycle.changed"
        ):
            try:
                import sys
                from pathlib import Path
                _root = Path(__file__).resolve().parents[4]
                if str(_root) not in sys.path:
                    sys.path.insert(0, str(_root))
                from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
                publish_event({
                    "event_type": "enrollment.completed",
                    "tenant_id": event.tenant_id,
                    "enrollment_id": event.payload.get("id") or event.payload.get("enrollment_id", ""),
                    "learner_id": event.payload.get("learner_id", ""),
                    "course_id": event.payload.get("course_id", ""),
                    "correlation_id": event.correlation_id,
                    "producer": "enrollment-service",
                })
            except Exception:
                pass  # best-effort — must not block enrollment transitions


class InMemoryObservabilityHook:
    def __init__(self) -> None:
        self.metrics: dict[str, float] = {}

    def observe(self, metric_name: str, value: float = 1.0) -> None:
        self.metrics[metric_name] = self.metrics.get(metric_name, 0.0) + value


class EnrollmentService:
    def __init__(
        self,
        store: EnrollmentStore,
        audit_log: AuditLogStore,
        event_publisher: EventPublisher,
        observability: ObservabilityHook,
    ) -> None:
        self.store = store
        self.audit_log = audit_log
        self.event_publisher = event_publisher
        self.observability = observability

    def create_enrollment(self, context: TenantContext, request: EnrollmentCreateRequest) -> Enrollment:
        start = perf_counter()
        existing = self.store.active_for_learner_course(context.tenant_id, request.learner_id, request.course_id)
        if existing:
            raise ConflictError("active enrollment already exists for learner and course")

        enrollment = Enrollment(
            tenant_id=context.tenant_id,
            learner_id=request.learner_id,
            course_id=request.course_id,
            assigned_by=context.actor_id,
            assignment_source=request.assignment_source,
            cohort_id=request.cohort_id,
            session_id=request.session_id,
        )
        created = self.store.create(enrollment)
        self._audit(context, "enrollment.created", created, {"source": request.assignment_source})
        self._publish("enrollment.lifecycle.changed", created, actor_id=context.actor_id, change_reason="created")
        self.observability.observe("enrollment.create.count")
        self.observability.observe("enrollment.create.latency_ms", (perf_counter() - start) * 1000)
        return created

    def get_enrollment(self, context: TenantContext, enrollment_id: str) -> Enrollment:
        enrollment = self.store.get(context.tenant_id, enrollment_id)
        if not enrollment:
            raise NotFoundError(f"enrollment '{enrollment_id}' not found")
        self.observability.observe("enrollment.read.count")
        return enrollment

    def list_enrollments(
        self,
        context: TenantContext,
        learner_id: str | None = None,
        course_id: str | None = None,
        status: str | None = None,
    ) -> list[Enrollment]:
        self.observability.observe("enrollment.list.count")
        return self.store.list(
            tenant_id=context.tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            status=status,
        )

    def transition_status(
        self,
        context: TenantContext,
        enrollment_id: str,
        to_status: EnrollmentStatus,
        reason: str,
    ) -> Enrollment:
        enrollment = self.get_enrollment(context, enrollment_id)
        from_status = enrollment.status
        try:
            enrollment.transition_to(to_status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        updated = self.store.update(enrollment)
        self._audit(
            context,
            "enrollment.status_transitioned",
            updated,
            {"from": from_status.value, "to": to_status.value, "reason": reason},
        )
        self._publish(
            "enrollment.lifecycle.changed",
            updated,
            actor_id=context.actor_id,
            change_reason=reason,
            from_status=from_status.value,
        )
        self.observability.observe("enrollment.transition.count")
        return updated

    def list_audit_logs(self, context: TenantContext) -> list[AuditLogEntry]:
        return self.audit_log.list(context.tenant_id)

    def _publish(self, event_type: str, enrollment: Enrollment, actor_id: str, change_reason: str, from_status: str | None = None) -> None:
        payload = asdict(enrollment)
        payload["status"] = enrollment.status.value
        payload["actor_id"] = actor_id
        payload["change_reason"] = change_reason
        if from_status:
            payload["from_status"] = from_status
        self.event_publisher.publish(
            Event(
                event_id=str(uuid4()),
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                tenant_id=enrollment.tenant_id,
                correlation_id=str(uuid4()),
                payload=payload,
                metadata={"aggregate_id": enrollment.id, "producer": "enrollment-service"},
            )
        )

    def _audit(self, context: TenantContext, action: str, enrollment: Enrollment, metadata: dict) -> None:
        self.audit_log.append(
            AuditLogEntry(
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
                action=action,
                enrollment_id=enrollment.id,
                metadata=metadata,
            )
        )
