"""Event consumers for enrollment-service (FA-024).

Spec §7 — Events Consumed:
- lms.user.created / lms.user.status.changed (from user-service)
- lms.course.published / lms.course.archived (from course-service)
- cohort.* events (from cohort-service)
- lms.session.* events (from session-service)
- progress.* events (from progress-service)
"""

from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("enrollment-service.consumers")


def _on_course_archived(event: EventEnvelope) -> None:
    """On course archived — log; future: transition active enrollments to expired."""
    course_id = event.payload.get("course_id") or event.payload.get("entity_id", "")
    logger.info("enrollment-service: course archived — tenant=%s course=%s", event.tenant_id, course_id)


def _on_course_published(event: EventEnvelope) -> None:
    """On course published — log; future: activate pending assignments."""
    course_id = event.payload.get("course_id") or event.payload.get("entity_id", "")
    logger.info("enrollment-service: course published — tenant=%s course=%s", event.tenant_id, course_id)


def _on_user_status_changed(event: EventEnvelope) -> None:
    """On user status changed — log; future: suspend enrollments for terminated users."""
    user_id = event.payload.get("user_id", "")
    to_status = event.payload.get("new_status") or event.payload.get("to", "")
    logger.info("enrollment-service: user status changed — tenant=%s user=%s to=%s", event.tenant_id, user_id, to_status)


def _on_user_deactivated(event: EventEnvelope) -> None:
    """On user deactivated — log; future: drop active/pending enrollments."""
    logger.info("enrollment-service: user.deactivated received — tenant=%s", event.tenant_id)


def _on_cohort_changed(event: EventEnvelope) -> None:
    """On cohort membership/deletion — log; future: reconcile cohort_id linkage."""
    logger.info("enrollment-service: cohort event received — tenant=%s", event.tenant_id)


def _on_progress_completed(event: EventEnvelope) -> None:
    """On progress.course_completed — log; future: auto-transition enrollment to completed."""
    logger.info("enrollment-service: progress.course_completed received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all enrollment-service consumers on the default event bus.

    AUD-037: spec §6 requires subscriptions from user_service, course_service,
    cohort_service, session_service, and progress_service.
    """
    bus = get_default_bus()
    # course events (course-service uses lms-prefixed names; subscribe both for resilience)
    bus.subscribe("lms.course.archived.v1", _on_course_archived)
    bus.subscribe("course.archived", _on_course_archived)
    bus.subscribe("lms.course.published.v1", _on_course_published)
    bus.subscribe("course.published", _on_course_published)
    # user events (canonical names per user-service-spec §6)
    bus.subscribe("user.status_changed", _on_user_status_changed)
    bus.subscribe("user.deactivated", _on_user_deactivated)
    # cohort events
    bus.subscribe("cohort.membership_added", _on_cohort_changed)
    bus.subscribe("cohort.deleted", _on_cohort_changed)
    bus.subscribe("cohort.closed", _on_cohort_changed)
    # progress events
    bus.subscribe("progress.course_completed", _on_progress_completed)
    logger.info("enrollment-service: event consumers registered (10 subscriptions)")
