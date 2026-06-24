"""Event consumers for workflow-engine (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("workflow-engine.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: trigger enrollment workflow."""
    logger.info("workflow-engine: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)

def _on_assessment_graded(event: EventEnvelope) -> None:
    """On assessment.graded.v1 — log; future: trigger completion workflow."""
    logger.info("workflow-engine: assessment.graded.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all workflow-engine consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    bus.subscribe("assessment.graded", _on_assessment_graded)
    logger.info("workflow-engine: event consumers registered")
