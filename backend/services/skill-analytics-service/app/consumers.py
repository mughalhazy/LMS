"""Event consumers for skill-analytics-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("skill-analytics-service.consumers")

def _on_assessment_graded(event: EventEnvelope) -> None:
    """On assessment.graded.v1 — log; future: update skill proficiency."""
    logger.info("skill-analytics-service: assessment.graded.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all skill-analytics-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("assessment.graded", _on_assessment_graded)
    logger.info("skill-analytics-service: event consumers registered")
