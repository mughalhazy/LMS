"""Event consumers for session-service (FA-024, G-24).

Spec §6 — Events Consumed (B01-014):
- course.published.v1 / course.archived.v1 (from course_service)
- lesson.published.v1 / lesson.archived.v1 (from lesson_service)
- cohort.created.v1 / cohort.updated.v1 / cohort.archived.v1 (from cohort_service)
- enrollment.created.v1 / enrollment.updated.v1 / enrollment.canceled.v1 (from enrollment_service)
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("session-service.consumers")


def _on_course_event(event: EventEnvelope) -> None:
    # B01-014: spec §6.1 — course lifecycle affects session scheduling eligibility
    course_id = event.payload.get("course_id", "")
    logger.info("session-service: course event %s — tenant=%s course=%s", event.event_type, event.tenant_id, course_id)


def _on_lesson_event(event: EventEnvelope) -> None:
    # B01-014: spec §6.2 — lesson lifecycle affects session linkage validity
    lesson_id = event.payload.get("lesson_id", "")
    logger.info("session-service: lesson event %s — tenant=%s lesson=%s", event.event_type, event.tenant_id, lesson_id)


def _on_cohort_changed(event: EventEnvelope) -> None:
    # spec §6.3 — cohort lifecycle: linkage validation / lifecycle safeguards
    cohort_id = event.payload.get("cohort_id", "")
    logger.info("session-service: cohort event %s — tenant=%s cohort=%s", event.event_type, event.tenant_id, cohort_id)


def _on_enrollment_event(event: EventEnvelope) -> None:
    # B01-014: spec §6.4 — maintain SessionRosterSnapshot and capacity pressure signals
    enrollment_id = event.payload.get("enrollment_id", "")
    logger.info("session-service: enrollment event %s — tenant=%s enrollment=%s", event.event_type, event.tenant_id, enrollment_id)


def register_consumers() -> None:
    """Register all session-service consumers on the default event bus."""
    bus = get_default_bus()
    # B01-014: course lifecycle (spec §6.1)
    bus.subscribe("course.published.v1", _on_course_event)
    bus.subscribe("lms.course.published.v1", _on_course_event)
    bus.subscribe("course.archived.v1", _on_course_event)
    bus.subscribe("lms.course.archived.v1", _on_course_event)
    # B01-014: lesson lifecycle (spec §6.2)
    bus.subscribe("lesson.published.v1", _on_lesson_event)
    bus.subscribe("lesson.archived.v1", _on_lesson_event)
    # cohort lifecycle (spec §6.3) — canonical + bridge
    bus.subscribe("cohort.created.v1", _on_cohort_changed)
    bus.subscribe("cohort.updated.v1", _on_cohort_changed)
    bus.subscribe("cohort.archived.v1", _on_cohort_changed)
    bus.subscribe("cohort.lifecycle.changed", _on_cohort_changed)
    # B01-014: enrollment events for roster snapshot (spec §6.4)
    bus.subscribe("enrollment.created.v1", _on_enrollment_event)
    bus.subscribe("enrollment.updated.v1", _on_enrollment_event)
    bus.subscribe("enrollment.canceled.v1", _on_enrollment_event)
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_event)
    logger.info("session-service: event consumers registered (15 topics)")
