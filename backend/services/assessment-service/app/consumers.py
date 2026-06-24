"""Event consumers for assessment-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("assessment-service.consumers")

def _on_enrollment_created(event: EventEnvelope) -> None:
    """On lms.enrollment.created.v1 — log; future: seed empty gradebook."""
    logger.info("assessment-service: lms.enrollment.created.v1 received — tenant=%s", event.tenant_id)

def _on_course_archived(event: EventEnvelope) -> None:
    """On lms.course.archived.v1 — log; future: expire active assessments."""
    logger.info("assessment-service: lms.course.archived.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all assessment-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("lms.enrollment.created.v1", _on_enrollment_created)
    bus.subscribe("lms.course.archived.v1", _on_course_archived)
    logger.info("assessment-service: event consumers registered")
