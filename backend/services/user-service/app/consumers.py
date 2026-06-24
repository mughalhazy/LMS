"""Event consumers for user-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("user-service.consumers")

def _on_login_succeeded(event: EventEnvelope) -> None:
    """On auth.login.succeeded.v1 — log; future: update user last_login_at."""
    logger.info("user-service: auth.login.succeeded.v1 received — tenant=%s", event.tenant_id)

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: update learner progress state."""
    logger.info("user-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)


def _on_rbac_assignments_changed(event: EventEnvelope) -> None:
    """On rbac.assignments.changed — log; future: refresh role linkage cache."""
    logger.info("user-service: rbac.assignments.changed received — tenant=%s", event.tenant_id)


def _on_institution_membership_changed(event: EventEnvelope) -> None:
    """On institution.membership.changed — log; future: update org_id/department/manager links."""
    logger.info("user-service: institution.membership.changed received — tenant=%s", event.tenant_id)


def _on_tenant_deactivated(event: EventEnvelope) -> None:
    """On tenant.deactivated — log; future: bulk-move active users to deactivated."""
    logger.info("user-service: tenant.deactivated received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all user-service consumers on the default event bus.

    AUD-039: spec §7 requires auth.login.succeeded, rbac.assignments.changed,
    institution.membership.changed, tenant.deactivated.
    enrollment.lifecycle.changed removed — not in spec §7.
    """
    bus = get_default_bus()
    bus.subscribe("auth.login.succeeded.v1", _on_login_succeeded)
    bus.subscribe("rbac.assignments.changed", _on_rbac_assignments_changed)
    bus.subscribe("institution.membership.changed", _on_institution_membership_changed)
    bus.subscribe("tenant.deactivated", _on_tenant_deactivated)
    logger.info("user-service: event consumers registered (4 subscriptions)")
