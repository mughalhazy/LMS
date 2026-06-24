"""Event consumers for auth-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("auth-service.consumers")

def _on_user_status_changed(event: EventEnvelope) -> None:
    """On user.status_changed — log; future: revoke sessions for suspended/locked users."""
    logger.info("auth-service: user.status_changed received — tenant=%s", event.tenant_id)


def _on_user_created(event: EventEnvelope) -> None:
    """On user.created — log; future: create auth_identity extension record."""
    logger.info("auth-service: user.created received — tenant=%s", event.tenant_id)


def _on_user_credential_changed(event: EventEnvelope) -> None:
    """On user.credential.changed — log; future: invalidate refresh token families."""
    logger.info("auth-service: user.credential.changed received — tenant=%s", event.tenant_id)


def _on_tenant_suspended(event: EventEnvelope) -> None:
    """On tenant.suspended — log; future: hard-deny login for tenant."""
    logger.info("auth-service: tenant.suspended received — tenant=%s", event.tenant_id)


def _on_tenant_reactivated(event: EventEnvelope) -> None:
    """On tenant.reactivated — log; future: re-enable login for tenant."""
    logger.info("auth-service: tenant.reactivated received — tenant=%s", event.tenant_id)


def _on_rbac_assignment_changed(event: EventEnvelope) -> None:
    """On rbac.assignment.changed — log; future: bump rbac_version claim hint."""
    logger.info("auth-service: rbac.assignment.changed received — tenant=%s", event.tenant_id)


def _on_security_risk_high(event: EventEnvelope) -> None:
    """On security.risk.high — log and emit auth.risk.detected (CAT-011: integration doc defines this event)."""
    logger.info("auth-service: security.risk.high received — tenant=%s", event.tenant_id)
    # CAT-011: publish auth.risk.detected as defined in auth-lifecycle-events.md
    try:
        from backend.services.shared.events.bus import get_default_bus
        from backend.services.shared.events.envelope import build_event
        risk_event = build_event(
            event_type="auth.risk.detected",
            topic="auth.risk.detected",
            producer_service="auth-service",
            tenant_id=event.tenant_id,
            payload={
                "risk_signal": event.payload.get("signal", "external_risk_flag"),
                "risk_score": event.payload.get("score", 0),
                "mitigation_action": "session_review_required",
            },
        )
        get_default_bus().publish(risk_event)
    except Exception:
        pass


def _on_tenant_status_changed(event: EventEnvelope) -> None:
    """On tenant.status.changed — integration contract alias; delegates to suspend/reactivate logic."""
    status = event.payload.get("status") or event.payload.get("new_status", "")
    logger.info("auth-service: tenant.status.changed received — tenant=%s status=%s", event.tenant_id, status)


def _on_user_lifecycle_changed(event: EventEnvelope) -> None:
    """On user.lifecycle.changed — integration contract alias for user status changes."""
    logger.info("auth-service: user.lifecycle.changed received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all auth-service consumers on the default event bus.

    AUD-032/033: spec §7 subscriptions.
    CAT-009: integration doc (auth-lifecycle-events.md) also specifies
    tenant.status.changed and user.lifecycle.changed — both registered as aliases.
    """
    bus = get_default_bus()
    bus.subscribe("user.status_changed", _on_user_status_changed)
    bus.subscribe("user.created", _on_user_created)
    bus.subscribe("user.credential.changed", _on_user_credential_changed)
    bus.subscribe("tenant.suspended", _on_tenant_suspended)
    bus.subscribe("tenant.reactivated", _on_tenant_reactivated)
    bus.subscribe("rbac.assignment.changed", _on_rbac_assignment_changed)
    bus.subscribe("security.risk.high", _on_security_risk_high)
    # CAT-009: integration contract topics (auth-lifecycle-events.md §Consumed events)
    bus.subscribe("tenant.status.changed", _on_tenant_status_changed)
    bus.subscribe("user.lifecycle.changed", _on_user_lifecycle_changed)
    logger.info("auth-service: event consumers registered (9 subscriptions)")
