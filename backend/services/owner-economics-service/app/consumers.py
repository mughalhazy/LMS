"""Event consumers for owner-economics-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("owner-economics-service.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: update owner revenue share."""
    logger.info("owner-economics-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all owner-economics-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    logger.info("owner-economics-service: event consumers registered")
