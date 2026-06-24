"""Event consumers for notification-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("notification-service.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: send enrollment notification."""
    logger.info("notification-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)

def _on_assessment_graded(event: EventEnvelope) -> None:
    """On assessment.graded.v1 — log; future: send grade notification."""
    logger.info("notification-service: assessment.graded.v1 received — tenant=%s", event.tenant_id)

def _on_login_succeeded(event: EventEnvelope) -> None:
    """On auth.login.succeeded.v1 — log; future: send login notification if enabled."""
    logger.info("notification-service: auth.login.succeeded.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all notification-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    bus.subscribe("assessment.graded", _on_assessment_graded)
    bus.subscribe("auth.login.succeeded.v1", _on_login_succeeded)
    logger.info("notification-service: event consumers registered")
