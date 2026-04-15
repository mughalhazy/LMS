from __future__ import annotations

from typing import Dict


SESSION_EVENT_TYPES: Dict[str, str] = {
    "created": "session.created.v1",
    "updated": "session.updated.v1",
    "scheduled": "session.scheduled.v1",
    "rescheduled": "session.rescheduled.v1",
    "published": "session.published.v1",
    "started": "session.started.v1",
    "completed": "session.completed.v1",
    "canceled": "session.canceled.v1",
    "archived": "session.archived.v1",
    "cohorts_linked": "session.cohorts_linked.v1",
    "lesson_linked": "session.lesson_linked.v1",
    "course_linked": "session.course_linked.v1",
}
