"""Event consumers for hr-helpdesk-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("hr-helpdesk-service.consumers")

def _on_user_status_changed(event: EventEnvelope) -> None:
    """On lms.user.status.changed — log; future: open HR ticket on termination."""
    logger.info("hr-helpdesk-service: lms.user.status.changed received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all hr-helpdesk-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("user.status_changed", _on_user_status_changed)
    logger.info("hr-helpdesk-service: event consumers registered")
