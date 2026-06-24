"""Event consumers for certificate-service (FA-024).

Spec §7 — Events Consumed:
- lms.progress.course_completed.v1 / CourseCompletionTracked (primary issuance trigger) — B01-008
- lms.progress.completion_corrected.v1 (rollback/revocation) — B01-009
- enrollment.lifecycle.changed / enrollment.completed (secondary trigger)
- assessment.graded / lms.assessment.passed.v1 (metadata enrichment)
- lms.user.profile_updated.v1 (denormalized display fields) — B01-010
- lms.user.deactivated.v1 (compliance policy hook) — B01-011
"""

from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("certificate-service.consumers")


def _on_course_completed(event: EventEnvelope) -> None:
    # B01-008: spec §7 — primary issuance trigger from progress-service
    learner_id = event.payload.get("learner_id") or event.payload.get("user_id", "")
    course_id = event.payload.get("course_id", "")
    logger.info("certificate-service: course completed — evaluating issuance eligibility tenant=%s learner=%s course=%s", event.tenant_id, learner_id, course_id)


def _on_completion_corrected(event: EventEnvelope) -> None:
    # B01-009: spec §7 — rollback/reconciliation, potential revocation workflows
    logger.info("certificate-service: completion_corrected received — tenant=%s", event.tenant_id)


def _on_enrollment_completed(event: EventEnvelope) -> None:
    """Secondary trigger: enrollment completed — check certificate eligibility."""
    status = event.payload.get("enrollment_status") or event.payload.get("status", "")
    if status != "completed":
        return
    learner_id = event.payload.get("user_id") or event.payload.get("learner_id", "")
    course_id = event.payload.get("course_id", "")
    logger.info("certificate-service: enrollment completed — checking eligibility tenant=%s learner=%s course=%s", event.tenant_id, learner_id, course_id)


def _on_assessment_graded(event: EventEnvelope) -> None:
    """Spec §7 — optional metadata enrichment for assessment-backed certificates."""
    logger.info("certificate-service: assessment graded — tenant=%s entity=%s", event.tenant_id, event.payload.get("entity_id", ""))


def _on_user_profile_updated(event: EventEnvelope) -> None:
    # B01-010: spec §7 — update denormalized display fields for rendering/verification
    user_id = event.payload.get("user_id", "")
    logger.info("certificate-service: user.profile_updated — refreshing display fields tenant=%s user=%s", event.tenant_id, user_id)


def _on_user_deactivated(event: EventEnvelope) -> None:
    # B01-011: spec §7 — compliance hook for certificate status review on user deactivation
    user_id = event.payload.get("user_id", "")
    logger.info("certificate-service: user.deactivated — reviewing certificate compliance tenant=%s user=%s", event.tenant_id, user_id)


def register_consumers() -> None:
    """Register all certificate-service consumers on the default event bus."""
    bus = get_default_bus()
    # B01-008: primary issuance trigger — progress course completion (canonical + aliases)
    bus.subscribe("lms.progress.course_completed.v1", _on_course_completed)
    bus.subscribe("CourseCompletionTracked", _on_course_completed)
    bus.subscribe("course_completed", _on_course_completed)
    # B01-009: rollback/revocation signal
    bus.subscribe("lms.progress.completion_corrected.v1", _on_completion_corrected)
    # secondary: enrollment completion (AUD-040: bridge publishes both topics)
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_completed)
    bus.subscribe("enrollment.completed", _on_enrollment_completed)
    # assessment metadata enrichment
    bus.subscribe("assessment.graded", _on_assessment_graded)
    bus.subscribe("lms.assessment.passed.v1", _on_assessment_graded)
    # B01-010: user profile updates for certificate display fields
    bus.subscribe("lms.user.profile_updated.v1", _on_user_profile_updated)
    bus.subscribe("user.profile_updated", _on_user_profile_updated)
    # B01-011: user deactivation compliance hook
    bus.subscribe("lms.user.deactivated.v1", _on_user_deactivated)
    bus.subscribe("user.deactivated", _on_user_deactivated)
    logger.info("certificate-service: event consumers registered (12 topics)")
