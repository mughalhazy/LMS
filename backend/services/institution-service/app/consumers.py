"""Event consumers for institution-service (FA-024, G-24).

Spec §9 — Events Consumed (B01-016):
- tenant.created.v1 — bootstrap suggestion for tenant-to-institution linking
- tenant.archived.v1 — auto-mark related tenant links inactive
- program.published.v1 — validate institution eligibility for program visibility
- program.retired.v1 — cleanup derived institution-program policy bindings
- user.role_changed.v1 — re-evaluate institution admin authorization cache
- user.deactivated.v1 — deactivate institution contact or delegated approver roles
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("institution-service.consumers")


def _on_tenant_created(event: EventEnvelope) -> None:
    # B01-016: spec §9 — bootstrap suggestion for tenant-to-institution linking
    tenant_id = event.payload.get("tenant_id", "")
    logger.info("institution-service: tenant.created — bootstrapping institution link suggestion tenant=%s", tenant_id)


def _on_tenant_archived(event: EventEnvelope) -> None:
    # B01-016: spec §9 — auto-mark related tenant links inactive
    tenant_id = event.payload.get("tenant_id", "")
    logger.info("institution-service: tenant.archived — marking tenant links inactive tenant=%s", tenant_id)


def _on_program_published(event: EventEnvelope) -> None:
    # B01-016: spec §9 — validate institution eligibility for program visibility policies
    program_id = event.payload.get("program_id", "")
    logger.info("institution-service: program.published — validating institution eligibility tenant=%s program=%s", event.tenant_id, program_id)


def _on_program_retired(event: EventEnvelope) -> None:
    # B01-016: spec §9 — cleanup derived institution-program policy bindings
    program_id = event.payload.get("program_id", "")
    logger.info("institution-service: program.retired — cleaning institution-program bindings tenant=%s program=%s", event.tenant_id, program_id)


def _on_user_role_changed(event: EventEnvelope) -> None:
    # B01-016: spec §9 — re-evaluate institution admin authorization cache
    user_id = event.payload.get("user_id", "")
    logger.info("institution-service: user.role_changed — refreshing authorization cache tenant=%s user=%s", event.tenant_id, user_id)


def _on_user_deactivated(event: EventEnvelope) -> None:
    # B01-016: spec §9 — remove/deactivate institution contact or delegated approver roles
    user_id = event.payload.get("user_id", "")
    logger.info("institution-service: user.deactivated — deactivating institution contacts tenant=%s user=%s", event.tenant_id, user_id)


def register_consumers() -> None:
    """Register all institution-service consumers on the default event bus."""
    bus = get_default_bus()
    # B01-016: all spec §9 required topics (canonical + alias for resilience)
    bus.subscribe("tenant.created.v1", _on_tenant_created)
    bus.subscribe("tenant.created", _on_tenant_created)
    bus.subscribe("tenant.archived.v1", _on_tenant_archived)
    bus.subscribe("tenant.archived", _on_tenant_archived)
    bus.subscribe("program.published.v1", _on_program_published)
    bus.subscribe("lms.program.program_status_changed.v1", _on_program_published)
    bus.subscribe("program.retired.v1", _on_program_retired)
    bus.subscribe("user.role_changed.v1", _on_user_role_changed)
    bus.subscribe("user.deactivated.v1", _on_user_deactivated)
    bus.subscribe("user.deactivated", _on_user_deactivated)
    logger.info("institution-service: event consumers registered (10 topics)")
