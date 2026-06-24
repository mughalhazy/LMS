"""Event consumers for feature-flag-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("feature-flag-service.consumers")

def _on_login_succeeded(event: EventEnvelope) -> None:
    """On auth.login.succeeded.v1 — log; future: refresh flag context for user."""
    logger.info("feature-flag-service: auth.login.succeeded.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all feature-flag-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("auth.login.succeeded.v1", _on_login_succeeded)
    logger.info("feature-flag-service: event consumers registered")
