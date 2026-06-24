"""Event consumers for course-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("course-service.consumers")

def _on_enrollment_created(event: EventEnvelope) -> None:
    """On lms.enrollment.created.v1 — log; future: increment enrollment_count."""
    logger.info("course-service: lms.enrollment.created.v1 received — tenant=%s", event.tenant_id)

def _on_lesson_created(event: EventEnvelope) -> None:
    """On lms.lesson.created.v1 — log; future: increment lesson_count."""
    logger.info("course-service: lms.lesson.created.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all course-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("lms.enrollment.created.v1", _on_enrollment_created)
    bus.subscribe("lms.lesson.created.v1", _on_lesson_created)
    logger.info("course-service: event consumers registered")
