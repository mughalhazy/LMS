"""Event consumers for capability-registry (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("capability-registry.consumers")

def _on_enrollment_created(event: EventEnvelope) -> None:
    """On lms.enrollment.created.v1 — log; future: verify capability gate."""
    logger.info("capability-registry: lms.enrollment.created.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all capability-registry consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("lms.enrollment.created.v1", _on_enrollment_created)
    logger.info("capability-registry: event consumers registered")
