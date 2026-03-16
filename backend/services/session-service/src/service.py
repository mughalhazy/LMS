from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from .events import SESSION_EVENT_TYPES
from .models import (
    AuditLog,
    DeliveryMetadata,
    DeliveryMode,
    EventMessage,
    RescheduleRecord,
    Session,
    SessionSchedule,
    SessionStatus,
)
from .repository import SessionRepository


class SessionServiceError(Exception):
    pass


class SessionNotFoundError(SessionServiceError):
    pass


class TenantBoundaryError(SessionServiceError):
    pass


class InvalidSessionTransitionError(SessionServiceError):
    pass


class SessionValidationError(SessionServiceError):
    pass


class SessionService:
    _transitions = {
        SessionStatus.DRAFT: {SessionStatus.SCHEDULED, SessionStatus.CANCELED, SessionStatus.ARCHIVED},
        SessionStatus.SCHEDULED: {SessionStatus.LIVE, SessionStatus.CANCELED, SessionStatus.ARCHIVED},
        SessionStatus.LIVE: {SessionStatus.COMPLETED, SessionStatus.CANCELED},
        SessionStatus.COMPLETED: {SessionStatus.ARCHIVED},
        SessionStatus.CANCELED: {SessionStatus.ARCHIVED},
        SessionStatus.ARCHIVED: set(),
    }

    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository
        self._metrics: Dict[str, int] = {
            "sessions_created": 0,
            "schedule_updates": 0,
            "status_transitions": 0,
            "events_published": 0,
            "audit_logs_written": 0,
        }

    def create_session(
        self,
        *,
        tenant_id: str,
        created_by: str,
        title: str,
        course_id: str,
        delivery_mode: str,
        description: Optional[str] = None,
        lesson_id: Optional[str] = None,
        cohort_ids: Optional[List[str]] = None,
        instructor_refs: Optional[List[str]] = None,
        capacity: Optional[int] = None,
        waitlist_enabled: bool = False,
        delivery_metadata: Optional[Dict] = None,
    ) -> Session:
        if not course_id:
            raise SessionValidationError("course_id is required")
        metadata = DeliveryMetadata(**(delivery_metadata or {}))
        self._validate_delivery_metadata(DeliveryMode(delivery_mode), metadata)

        session = Session(
            session_id=str(uuid4()),
            tenant_id=tenant_id,
            status=SessionStatus.DRAFT,
            title=title,
            description=description,
            course_id=course_id,
            lesson_id=lesson_id,
            cohort_ids=cohort_ids or [],
            delivery_mode=DeliveryMode(delivery_mode),
            instructor_refs=instructor_refs or [],
            capacity=capacity,
            waitlist_enabled=waitlist_enabled,
            delivery_metadata=metadata,
            created_by=created_by,
            updated_by=created_by,
        )
        self.repository.create(session)
        self._metrics["sessions_created"] += 1
        self._record_audit(session, "session.created", created_by, {"course_id": course_id})
        self._publish_event("created", session, {"status": session.status.value})
        return session

    def get_session(self, *, tenant_id: str, session_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        return session

    def update_session(
        self,
        *,
        tenant_id: str,
        session_id: str,
        updated_by: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        instructor_refs: Optional[List[str]] = None,
        capacity: Optional[int] = None,
        waitlist_enabled: Optional[bool] = None,
        delivery_metadata: Optional[Dict] = None,
    ) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        metadata = session.delivery_metadata
        if delivery_metadata is not None:
            metadata = DeliveryMetadata(**delivery_metadata)
            self._validate_delivery_metadata(session.delivery_mode, metadata)

        updated = replace(
            session,
            title=title if title is not None else session.title,
            description=description if description is not None else session.description,
            instructor_refs=instructor_refs if instructor_refs is not None else session.instructor_refs,
            capacity=capacity if capacity is not None else session.capacity,
            waitlist_enabled=waitlist_enabled if waitlist_enabled is not None else session.waitlist_enabled,
            delivery_metadata=metadata,
            updated_by=updated_by,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._record_audit(updated, "session.updated", updated_by, {"version": updated.version})
        self._publish_event("updated", updated, {"version": updated.version})
        return updated

    def schedule_session(
        self,
        *,
        tenant_id: str,
        session_id: str,
        scheduled_by: str,
        timezone_name: str,
        start_at: datetime,
        end_at: datetime,
        recurrence_rule: Optional[str] = None,
        reason: str = "schedule update",
        force: bool = False,
    ) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        self._validate_schedule(timezone_name, start_at, end_at)

        if session.status in {SessionStatus.COMPLETED, SessionStatus.ARCHIVED}:
            raise SessionValidationError("cannot schedule completed or archived sessions")
        if session.status == SessionStatus.LIVE and not force:
            raise SessionValidationError("force=true required to reschedule a live session")

        schedule = SessionSchedule(
            timezone=timezone_name,
            start_at=self._ensure_utc(start_at),
            end_at=self._ensure_utc(end_at),
            recurrence_rule=recurrence_rule,
        )

        history = session.reschedule_history.copy()
        event_key = "scheduled"
        if session.schedule:
            history.append(
                RescheduleRecord(
                    previous_start_at=session.schedule.start_at,
                    previous_end_at=session.schedule.end_at,
                    new_start_at=schedule.start_at,
                    new_end_at=schedule.end_at,
                    actor_id=scheduled_by,
                    reason=reason,
                )
            )
            event_key = "rescheduled"

        next_status = session.status
        if session.status == SessionStatus.DRAFT:
            next_status = SessionStatus.SCHEDULED

        updated = replace(
            session,
            status=next_status,
            schedule=schedule,
            reschedule_history=history,
            updated_by=scheduled_by,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._metrics["schedule_updates"] += 1
        self._record_audit(
            updated,
            "session.scheduled" if event_key == "scheduled" else "session.rescheduled",
            scheduled_by,
            {"reason": reason, "force": force},
        )
        self._publish_event(event_key, updated, {"reason": reason})
        return updated

    def publish_session(self, *, tenant_id: str, session_id: str, actor_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        if session.status != SessionStatus.DRAFT:
            raise InvalidSessionTransitionError(f"cannot publish from {session.status.value}")
        if session.schedule is None:
            raise SessionValidationError("session schedule is required before publish")
        return self._transition(session, SessionStatus.SCHEDULED, actor_id, "published")

    def start_session(self, *, tenant_id: str, session_id: str, actor_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        if session.schedule is None:
            raise SessionValidationError("session schedule is required before start")
        updated = self._transition(session, SessionStatus.LIVE, actor_id, "started")
        updated.actual_start_at = datetime.utcnow()
        self.repository.update(updated)
        return updated

    def complete_session(self, *, tenant_id: str, session_id: str, actor_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        updated = self._transition(session, SessionStatus.COMPLETED, actor_id, "completed")
        updated.actual_end_at = datetime.utcnow()
        self.repository.update(updated)
        return updated

    def cancel_session(self, *, tenant_id: str, session_id: str, actor_id: str, reason: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        updated = self._transition(session, SessionStatus.CANCELED, actor_id, "canceled")
        self._record_audit(updated, "session.canceled.reason", actor_id, {"reason": reason})
        return updated

    def archive_session(self, *, tenant_id: str, session_id: str, actor_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        return self._transition(session, SessionStatus.ARCHIVED, actor_id, "archived")

    def link_course(self, *, tenant_id: str, session_id: str, actor_id: str, course_id: str) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        if session.status in {SessionStatus.LIVE, SessionStatus.COMPLETED, SessionStatus.CANCELED, SessionStatus.ARCHIVED}:
            raise SessionValidationError("course linkage can only be changed while draft/scheduled")
        updated = replace(
            session,
            course_id=course_id,
            updated_by=actor_id,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._record_audit(updated, "session.course_linked", actor_id, {"course_id": course_id})
        self._publish_event("course_linked", updated, {"course_id": course_id})
        return updated

    def link_lesson(self, *, tenant_id: str, session_id: str, actor_id: str, lesson_id: Optional[str]) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        updated = replace(
            session,
            lesson_id=lesson_id,
            updated_by=actor_id,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._record_audit(updated, "session.lesson_linked", actor_id, {"lesson_id": lesson_id})
        self._publish_event("lesson_linked", updated, {"lesson_id": lesson_id})
        return updated

    def link_cohorts(self, *, tenant_id: str, session_id: str, actor_id: str, cohort_ids: List[str]) -> Session:
        session = self._get_scoped_session(tenant_id, session_id)
        updated = replace(
            session,
            cohort_ids=sorted(set(cohort_ids)),
            updated_by=actor_id,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._record_audit(updated, "session.cohorts_linked", actor_id, {"cohort_ids": updated.cohort_ids})
        self._publish_event("cohorts_linked", updated, {"cohort_ids": updated.cohort_ids})
        return updated

    def list_sessions(
        self,
        *,
        tenant_id: str,
        status: Optional[str] = None,
        delivery_mode: Optional[str] = None,
        course_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
    ) -> List[Session]:
        return self.repository.list_by_filters(
            tenant_id=tenant_id,
            status=status,
            delivery_mode=delivery_mode,
            course_id=course_id,
            cohort_id=cohort_id,
            instructor_id=instructor_id,
        )

    def list_calendar(self, *, tenant_id: str) -> List[Dict]:
        calendar_rows: List[Dict] = []
        for session in self.repository.list_by_filters(tenant_id=tenant_id):
            if session.schedule is None:
                continue
            calendar_rows.append(
                {
                    "session_id": session.session_id,
                    "title": session.title,
                    "course_id": session.course_id,
                    "cohort_ids": session.cohort_ids,
                    "timezone": session.schedule.timezone,
                    "start_at": session.schedule.start_at.isoformat(),
                    "end_at": session.schedule.end_at.isoformat(),
                    "delivery_mode": session.delivery_mode.value,
                    "status": session.status.value,
                    "recurrence_rule": session.schedule.recurrence_rule,
                }
            )
        return sorted(calendar_rows, key=lambda row: row["start_at"])

    def observability_snapshot(self) -> Dict[str, int]:
        return dict(self._metrics)

    def _transition(self, session: Session, target: SessionStatus, actor_id: str, event_name: str) -> Session:
        allowed = self._transitions[session.status]
        if target not in allowed:
            raise InvalidSessionTransitionError(f"Cannot transition {session.status.value} -> {target.value}")

        updated = replace(
            session,
            status=target,
            updated_by=actor_id,
            updated_at=datetime.utcnow(),
            version=session.version + 1,
        )
        self.repository.update(updated)
        self._metrics["status_transitions"] += 1
        self._record_audit(updated, f"session.{event_name}", actor_id, {"status": target.value})
        self._publish_event(event_name, updated, {"status": target.value})
        return updated

    def _get_scoped_session(self, tenant_id: str, session_id: str) -> Session:
        session = self.repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"session {session_id} not found")
        if session.tenant_id != tenant_id:
            raise TenantBoundaryError("cross-tenant access denied")
        return session

    def _record_audit(self, session: Session, action: str, actor_id: str, details: Dict) -> None:
        self.repository.append_audit_log(
            AuditLog(
                audit_id=str(uuid4()),
                tenant_id=session.tenant_id,
                session_id=session.session_id,
                action=action,
                actor_id=actor_id,
                details=details,
            )
        )
        self._metrics["audit_logs_written"] += 1

    def _publish_event(self, action: str, session: Session, payload: Dict) -> None:
        envelope = {
            "session_id": session.session_id,
            "status": session.status.value,
            "course_id": session.course_id,
            "lesson_id": session.lesson_id,
            "cohort_ids": session.cohort_ids,
            "delivery_mode": session.delivery_mode.value,
            "version": session.version,
            "updated_at": session.updated_at.isoformat(),
        }
        envelope.update(payload)
        self.repository.append_event(
            EventMessage(
                event_id=str(uuid4()),
                event_type=SESSION_EVENT_TYPES[action],
                tenant_id=session.tenant_id,
                aggregate_id=session.session_id,
                payload=envelope,
            )
        )
        self._metrics["events_published"] += 1

    def _validate_schedule(self, timezone_name: str, start_at: datetime, end_at: datetime) -> None:
        if end_at <= start_at:
            raise SessionValidationError("end_at must be after start_at")
        try:
            ZoneInfo(timezone_name)
        except Exception as exc:  # pragma: no cover - defensive
            raise SessionValidationError(f"invalid timezone {timezone_name}") from exc

    def _validate_delivery_metadata(self, mode: DeliveryMode, metadata: DeliveryMetadata) -> None:
        if mode == DeliveryMode.ONLINE:
            if not metadata.online_join_url:
                raise SessionValidationError("online mode requires online_join_url")
        if mode == DeliveryMode.IN_PERSON:
            if not {"building", "room", "address"}.issubset(set(metadata.location.keys())):
                raise SessionValidationError("in_person mode requires building, room, and address")
        if mode == DeliveryMode.HYBRID:
            if not metadata.online_join_url:
                raise SessionValidationError("hybrid mode requires online_join_url")
            if not {"building", "room", "address"}.issubset(set(metadata.location.keys())):
                raise SessionValidationError("hybrid mode requires in-person location")

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def session_to_dict(self, session: Session) -> Dict:
        payload = asdict(session)
        payload["status"] = session.status.value
        payload["delivery_mode"] = session.delivery_mode.value
        payload["created_at"] = session.created_at.isoformat()
        payload["updated_at"] = session.updated_at.isoformat()
        payload["actual_start_at"] = session.actual_start_at.isoformat() if session.actual_start_at else None
        payload["actual_end_at"] = session.actual_end_at.isoformat() if session.actual_end_at else None
        if session.schedule:
            payload["schedule"]["start_at"] = session.schedule.start_at.isoformat()
            payload["schedule"]["end_at"] = session.schedule.end_at.isoformat()
        for row in payload["reschedule_history"]:
            row["changed_at"] = row["changed_at"].isoformat()
            row["previous_start_at"] = row["previous_start_at"].isoformat()
            row["previous_end_at"] = row["previous_end_at"].isoformat()
            row["new_start_at"] = row["new_start_at"].isoformat()
            row["new_end_at"] = row["new_end_at"].isoformat()
        return payload
