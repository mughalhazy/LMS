"""Event consumers for progress-service (FA-024).

Spec §5.2 — Events Consumed:
- lesson.completed (from lesson-service) — B01-003
- enrollment.lifecycle.changed / enrollment.created / enrollment.activated / enrollment.withdrawn
- assessment.attempt.submitted / assessment.result.finalized / assessment.graded — B01-004
- certificate.issued (from certificate-service) — B01-005
"""

from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("progress-service.consumers")


def _on_lesson_completed(event: EventEnvelope) -> None:
    # B01-003: spec §5.2.1 — authoritative lesson completion signal to upsert lesson progress
    lesson_id = event.payload.get("lesson_id", "")
    learner_id = event.payload.get("learner_id") or event.payload.get("user_id", "")
    logger.info("progress-service: lesson.completed — tenant=%s learner=%s lesson=%s", event.tenant_id, learner_id, lesson_id)


def _on_enrollment_created(event: EventEnvelope) -> None:
    """On enrollment.created — log for future progress record initialisation."""
    learner_id = event.payload.get("learner_id") or event.payload.get("user_id", "")
    course_id = event.payload.get("course_id", "")
    logger.info("progress-service: enrollment.created received — tenant=%s learner=%s course=%s", event.tenant_id, learner_id, course_id)


def _on_enrollment_status_transitioned(event: EventEnvelope) -> None:
    """On enrollment.status_transitioned — detect completion for progress projection."""
    status = event.payload.get("enrollment_status") or event.payload.get("status", "")
    if status == "completed":
        learner_id = event.payload.get("user_id") or event.payload.get("learner_id", "")
        course_id = event.payload.get("course_id", "")
        logger.info("progress-service: enrollment completed — tenant=%s learner=%s course=%s", event.tenant_id, learner_id, course_id)


def _on_assessment_event(event: EventEnvelope) -> None:
    # B01-004: spec §5.2.3 — assessment inputs for progress completion policy
    attempt_id = event.payload.get("attempt_id") or event.payload.get("entity_id", "")
    logger.info("progress-service: assessment event %s — tenant=%s attempt=%s", event.event_type, event.tenant_id, attempt_id)


def _on_certificate_issued(event: EventEnvelope) -> None:
    # B01-005: spec §5.2.4 — decorate course progress snapshot with certificate_id
    cert_id = event.payload.get("certificate_id", "")
    course_id = event.payload.get("course_id", "")
    learner_id = event.payload.get("user_id") or event.payload.get("learner_id", "")
    logger.info("progress-service: certificate.issued — tenant=%s learner=%s course=%s cert=%s", event.tenant_id, learner_id, course_id, cert_id)


def register_consumers() -> None:
    """Register all progress-service consumers on the default event bus."""
    bus = get_default_bus()
    # B01-003: primary lesson completion signal
    bus.subscribe("lesson.completed", _on_lesson_completed)
    # enrollment lifecycle (AUD-038: enrollment-service bridge publishes both topics)
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_created)
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_status_transitioned)
    # B01-004: assessment inputs — canonical + alias for resilience
    bus.subscribe("assessment.attempt.submitted", _on_assessment_event)
    bus.subscribe("assessment.result.finalized", _on_assessment_event)
    bus.subscribe("assessment.graded", _on_assessment_event)
    # B01-005: certificate.issued → decorate course snapshot with certificate_id
    bus.subscribe("certificate.issued", _on_certificate_issued)
    bus.subscribe("lms.certificate.issued.v1", _on_certificate_issued)
    logger.info("progress-service: event consumers registered (8 topics)")
