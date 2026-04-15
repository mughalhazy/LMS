"""Shared segment runtime behavior layer — CGAP-083 / DF-06 boundary decision.

Architectural decision (resolved 2026-04-11):
  `UnifiedSegmentService` and its subclasses (`SegmentCourseRoster`,
  `SegmentProgressService`, `SegmentAssessmentService`,
  `SegmentNotificationService`) live in `shared/` intentionally.

Rationale:
  These are *behavior mixins*, not a standalone service. Each class is a thin
  capability-gated wrapper that delegates all config and entitlement lookups to
  `control_plane` (the authoritative capability chain). They hold no durable
  state of their own — subclass state (e.g., `student_ids`, `attendance`) is
  in-process only and owned by the calling service.

  Multiple services (academy-ops, system-of-record, exam-engine) compose these
  mixins to get consistent entitlement enforcement without duplicating the
  control-plane delegation pattern. Placing them in a dedicated service would
  require a network hop for what is essentially a policy-enforcement helper.

Boundary rule:
  - `shared/segment_runtime.py` MAY contain control-plane delegation helpers.
  - It MUST NOT contain persistence, external I/O, or business logic beyond
    capability gating and event emission.
  - Segment-specific business rules (e.g., fee structures, grading schemas) go
    in the relevant domain service — not here.

DF-06 status: RESOLVED — no code relocation required. Boundary is correct.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.control_plane import ControlPlaneClient, build_control_plane_client
from shared.models.config import ConfigResolutionContext
from shared.models.event import PlatformEvent
from shared.utils.entitlement import TenantEntitlementContext


@dataclass
class SegmentRuntimeContext:
    tenant: TenantEntitlementContext
    correlation_id: str


@dataclass
class UnifiedSegmentService:
    context: SegmentRuntimeContext
    control_plane: ControlPlaneClient | None = None

    def __post_init__(self) -> None:
        if self.control_plane is None:
            self.control_plane = build_control_plane_client()

    def _resolve_behavior(self) -> dict[str, Any]:
        effective = self.control_plane.get_config(
            ConfigResolutionContext(
                tenant_id=self.context.tenant.tenant_id,
                country_code=self.context.tenant.country_code,
                segment_id=self.context.tenant.segment_id,
            )
        )
        return dict(effective.behavior_tuning.get("segment_behavior", {}))

    def _is_capability_enabled(self, capability_id: str) -> bool:
        return self.control_plane.is_enabled(self.context.tenant, capability_id)

    def _event(self, event_type: str, payload: dict[str, Any]) -> PlatformEvent:
        return PlatformEvent(
            event_type=event_type,
            tenant_id=self.context.tenant.tenant_id,
            correlation_id=self.context.correlation_id,
            payload=payload,
        )


@dataclass
class SegmentCourseRoster(UnifiedSegmentService):
    student_ids: set[str] = field(default_factory=set)
    guardian_links: dict[str, set[str]] = field(default_factory=dict)
    cohort_members: dict[str, set[str]] = field(default_factory=dict)

    def enroll_student(self, student_id: str) -> PlatformEvent:
        if not self._is_capability_enabled("course.roster.enroll"):
            raise PermissionError("capability denied: course.roster.enroll")
        self.student_ids.add(student_id)
        return self._event("course.roster.student_enrolled", {"student_id": student_id})

    def add_guardian_link(self, *, student_id: str, guardian_id: str) -> PlatformEvent:
        if not self._is_capability_enabled("course.roster.guardian_link.write"):
            raise PermissionError("capability denied: course.roster.guardian_link.write")
        if student_id not in self.student_ids:
            raise ValueError("student must be enrolled before guardian linking")
        self.guardian_links.setdefault(student_id, set()).add(guardian_id)
        return self._event("course.roster.guardian_linked", {"student_id": student_id, "guardian_id": guardian_id})

    def assign_student_to_cohort(self, *, student_id: str, cohort_id: str) -> PlatformEvent:
        behavior = self._resolve_behavior()
        if not bool(behavior.get("cohort_enabled", False)):
            raise RuntimeError("segment behavior disabled: cohort_enabled")
        if student_id not in self.student_ids:
            raise ValueError("student must be enrolled before cohort assignment")
        self.cohort_members.setdefault(cohort_id, set()).add(student_id)
        return self._event("course.roster.student_assigned_to_cohort", {"student_id": student_id, "cohort_id": cohort_id})


@dataclass
class SegmentProgressService(UnifiedSegmentService):
    attendance: list[PlatformEvent] = field(default_factory=list)

    def record_attendance_checkpoint(self, *, checkpoint_id: str, student_id: str, course_id: str, state: str, period_key: str) -> PlatformEvent:
        behavior = self._resolve_behavior()
        if not bool(behavior.get("attendance_enabled", False)):
            raise RuntimeError("segment behavior disabled: attendance_enabled")
        if not self._is_capability_enabled("progress.attendance.record"):
            raise PermissionError("capability denied: progress.attendance.record")
        event = self._event(
            "progress.attendance.recorded",
            {
                "checkpoint_id": checkpoint_id,
                "student_id": student_id,
                "course_id": course_id,
                "state": state,
                "period_key": period_key,
            },
        )
        self.attendance.append(event)
        return event


@dataclass
class SegmentAssessmentService(UnifiedSegmentService):
    alerts: list[PlatformEvent] = field(default_factory=list)

    def record_score(self, *, student_id: str, course_id: str, score_percent: float, low_score_threshold: float = 60.0) -> PlatformEvent | None:
        if not self._is_capability_enabled("assessment.score.record"):
            raise PermissionError("capability denied: assessment.score.record")
        if score_percent >= low_score_threshold:
            return None
        event = self._event(
            "assessment.performance.alert",
            {
                "student_id": student_id,
                "course_id": course_id,
                "score_percent": score_percent,
                "low_score_threshold": low_score_threshold,
            },
        )
        self.alerts.append(event)
        return event


@dataclass
class SegmentNotificationService(UnifiedSegmentService):
    sent: list[PlatformEvent] = field(default_factory=list)

    def notify_guardians(self, *, guardian_ids: list[str], category: str, message: str, student_id: str, course_id: str) -> list[PlatformEvent]:
        behavior = self._resolve_behavior()
        if not bool(behavior.get("guardian_notifications_enabled", False)):
            raise RuntimeError("segment behavior disabled: guardian_notifications_enabled")
        capability_id = f"notification.guardian.{category}.send"
        if not self._is_capability_enabled(capability_id):
            raise PermissionError(f"capability denied: {capability_id}")
        events = [
            self._event(
                "notification.guardian.sent",
                {
                    "guardian_id": guardian_id,
                    "student_id": student_id,
                    "course_id": course_id,
                    "category": category,
                    "message": message,
                },
            )
            for guardian_id in sorted(set(guardian_ids))
        ]
        self.sent.extend(events)
        return events
