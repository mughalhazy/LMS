"""Event consumers for email-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("email-service.consumers")

def _on_user_created(event: EventEnvelope) -> None:
    """On user.created — future: trigger welcome_email via trigger rule."""
    logger.info("email-service: user.created received — tenant=%s", event.tenant_id)

def _on_password_reset(event: EventEnvelope) -> None:
    """On user.password_reset_requested — future: trigger password_reset email."""
    logger.info("email-service: user.password_reset_requested received — tenant=%s", event.tenant_id)

def _on_enrollment_created(event: EventEnvelope) -> None:
    """On course.enrollment.created — future: trigger course_enrollment email."""
    logger.info("email-service: course.enrollment.created received — tenant=%s", event.tenant_id)

def _on_deadline_approaching(event: EventEnvelope) -> None:
    """On learning.deadline.approaching — future: trigger deadline_reminder email."""
    logger.info("email-service: learning.deadline.approaching received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all email-service consumers on the default event bus.

    B05-001: topics aligned to spec §Default templates trigger events.
    """
    bus = get_default_bus()
    bus.subscribe("user.created", _on_user_created)
    bus.subscribe("user.password_reset_requested", _on_password_reset)
    bus.subscribe("course.enrollment.created", _on_enrollment_created)
    bus.subscribe("learning.deadline.approaching", _on_deadline_approaching)
    logger.info("email-service: event consumers registered")
