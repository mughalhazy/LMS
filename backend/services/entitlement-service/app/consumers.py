"""Event consumers for entitlement-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("entitlement-service.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: validate entitlement on enroll."""
    logger.info("entitlement-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)

def _on_billing_plan_changed(event: EventEnvelope) -> None:
    """B09-004: capability-gating-model §3.2 — on billing plan change, publish entitlement.updated."""
    logger.info("entitlement-service: billing.plan.changed — tenant=%s", event.tenant_id)
    try:
        from backend.services.shared.events.envelope import build_event
        updated = build_event(
            event_type="entitlement.updated",
            payload={"tenant_id": event.tenant_id, "trigger": "billing.plan.changed"},
            tenant_id=event.tenant_id,
            producer_service="entitlement-service",
        )
        get_default_bus().publish(updated)
    except Exception:
        pass  # best-effort


def _on_billing_suspended(event: EventEnvelope) -> None:
    """B09-004: subscription suspension triggers entitlement.updated cache invalidation."""
    logger.info("entitlement-service: billing.subscription.suspended — tenant=%s", event.tenant_id)
    try:
        from backend.services.shared.events.envelope import build_event
        updated = build_event(
            event_type="entitlement.updated",
            payload={"tenant_id": event.tenant_id, "trigger": "billing.subscription.suspended"},
            tenant_id=event.tenant_id,
            producer_service="entitlement-service",
        )
        get_default_bus().publish(updated)
    except Exception:
        pass  # best-effort


def register_consumers() -> None:
    """Register all entitlement-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    # B09-004: capability-gating-model §3.2 — plan lifecycle events from billing
    bus.subscribe("billing.plan.changed", _on_billing_plan_changed)
    bus.subscribe("billing.subscription.suspended", _on_billing_suspended)
    logger.info("entitlement-service: event consumers registered")
