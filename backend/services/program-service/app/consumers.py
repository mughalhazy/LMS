"""Event consumers for program-service (FA-024, G-24).

Spec §6 — Events Consumed (B01-012):
- lms.course.created.v1 — cache course existence for mapping validation
- lms.course.updated.v1 — refresh denormalized course title/status in read views
- lms.course.published.v1 — optional policy gate for mapped program courses
- lms.organization.institution_created.v1 — validate/link new institution references
- lms.cohort.cohort_created.v1 — non-owning reference projection for cohort counts
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("program-service.consumers")


def _on_course_created(event: EventEnvelope) -> None:
    # B01-012: spec §6.1 — cache course existence for faster mapping validation
    course_id = event.payload.get("course_id", "")
    logger.info("program-service: lms.course.created.v1 — tenant=%s course=%s", event.tenant_id, course_id)


def _on_course_updated(event: EventEnvelope) -> None:
    # B01-012: spec §6.2 — refresh denormalized course title/status in read views
    course_id = event.payload.get("course_id", "")
    logger.info("program-service: lms.course.updated.v1 — tenant=%s course=%s", event.tenant_id, course_id)


def _on_course_published(event: EventEnvelope) -> None:
    # B01-012: spec §6.3 — policy enforcement for mapped program courses
    course_id = event.payload.get("course_id", "")
    logger.info("program-service: lms.course.published.v1 — tenant=%s course=%s", event.tenant_id, course_id)


def _on_course_archived(event: EventEnvelope) -> None:
    # retained: flag mapped program if required course is archived
    logger.info("program-service: lms.course.archived.v1 — tenant=%s", event.tenant_id)


def _on_institution_created(event: EventEnvelope) -> None:
    # B01-012: spec §6.4 — validate/link new institution references
    institution_id = event.payload.get("institution_id", "")
    logger.info("program-service: institution_created — tenant=%s institution=%s", event.tenant_id, institution_id)


def _on_cohort_created(event: EventEnvelope) -> None:
    # B01-012: spec §6.5 — non-owning reference projection for cohort counts per program
    cohort_id = event.payload.get("cohort_id", "")
    logger.info("program-service: cohort_created — tenant=%s cohort=%s", event.tenant_id, cohort_id)


def register_consumers() -> None:
    """Register all program-service consumers on the default event bus."""
    bus = get_default_bus()
    # B01-012: spec §6 required topics
    bus.subscribe("lms.course.created.v1", _on_course_created)
    bus.subscribe("lms.course.updated.v1", _on_course_updated)
    bus.subscribe("lms.course.published.v1", _on_course_published)
    bus.subscribe("lms.course.archived.v1", _on_course_archived)
    bus.subscribe("lms.organization.institution_created.v1", _on_institution_created)
    bus.subscribe("institution.created.v1", _on_institution_created)
    bus.subscribe("lms.cohort.cohort_created.v1", _on_cohort_created)
    bus.subscribe("cohort.created", _on_cohort_created)
    logger.info("program-service: event consumers registered (8 topics)")
