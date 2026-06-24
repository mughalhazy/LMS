"""Event consumers for analytics-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("analytics-service.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: ingest analytics event."""
    logger.info("analytics-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)

def _on_assessment_graded(event: EventEnvelope) -> None:
    """On assessment.graded.v1 — log; future: ingest grade analytics."""
    logger.info("analytics-service: assessment.graded.v1 received — tenant=%s", event.tenant_id)

def _on_course_published(event: EventEnvelope) -> None:
    """On lms.course.published.v1 — log; future: ingest catalogue analytics."""
    logger.info("analytics-service: lms.course.published.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all analytics-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    bus.subscribe("assessment.graded", _on_assessment_graded)
    bus.subscribe("lms.course.published.v1", _on_course_published)
    logger.info("analytics-service: event consumers registered")
