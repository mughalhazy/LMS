"""Event consumers for group-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("group-service.consumers")

def _on_cohort_changed(event: EventEnvelope) -> None:
    """On cohort.lifecycle.changed — log; future: sync group membership."""
    logger.info("group-service: cohort.lifecycle.changed received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all group-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("cohort.lifecycle.changed", _on_cohort_changed)
    logger.info("group-service: event consumers registered")
