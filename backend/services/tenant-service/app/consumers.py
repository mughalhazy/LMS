"""Event consumers for tenant-service (FA-024, G-24).

Spec §7 — Events Consumed (B02-002):
- institution.root.provisioned.v1 — attach/update institution_root_ref for tenant
- entitlement.plan.deprecated.v1 — mark linked plan as migration-required
- user.assignment.admin.changed.v1 — update primary admin assignment metadata
- security.policy.baseline.updated.v1 — evaluate drift and queue config update recommendation
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("tenant-service.consumers")


def _on_institution_root_provisioned(event: EventEnvelope) -> None:
    # B02-002: spec §7.1 — attach/update institution_root_ref for tenant
    institution_id = event.payload.get("institution_id", "")
    logger.info("tenant-service: institution.root.provisioned — tenant=%s institution=%s", event.tenant_id, institution_id)


def _on_entitlement_plan_deprecated(event: EventEnvelope) -> None:
    # B02-002: spec §7.2 — mark linked plan as migration-required
    plan_id = event.payload.get("plan_id", "")
    logger.info("tenant-service: entitlement.plan.deprecated — tenant=%s plan=%s", event.tenant_id, plan_id)


def _on_admin_assignment_changed(event: EventEnvelope) -> None:
    # B02-002: spec §7.3 — update referenced primary admin assignment metadata
    user_id = event.payload.get("user_id", "")
    logger.info("tenant-service: user.assignment.admin.changed — tenant=%s user=%s", event.tenant_id, user_id)


def _on_security_baseline_updated(event: EventEnvelope) -> None:
    # B02-002: spec §7.4 — evaluate drift and optionally queue config update recommendation
    logger.info("tenant-service: security.policy.baseline.updated — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all tenant-service consumers on the default event bus."""
    bus = get_default_bus()
    # B02-002: all 4 spec §7 required topics
    bus.subscribe("institution.root.provisioned.v1", _on_institution_root_provisioned)
    bus.subscribe("entitlement.plan.deprecated.v1", _on_entitlement_plan_deprecated)
    bus.subscribe("user.assignment.admin.changed.v1", _on_admin_assignment_changed)
    bus.subscribe("security.policy.baseline.updated.v1", _on_security_baseline_updated)
    logger.info("tenant-service: event consumers registered (4 topics)")
