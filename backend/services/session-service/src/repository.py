from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional

from .models import AuditLog, EventMessage, Session


class SessionRepository:
    """Storage contract for session persistence."""

    def create(self, session: Session) -> Session:
        raise NotImplementedError

    def get(self, session_id: str) -> Optional[Session]:
        raise NotImplementedError

    def update(self, session: Session) -> Session:
        raise NotImplementedError

    def list_by_filters(
        self,
        *,
        tenant_id: str,
        status: Optional[str] = None,
        delivery_mode: Optional[str] = None,
        course_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
    ) -> List[Session]:
        raise NotImplementedError

    def append_audit_log(self, log: AuditLog) -> None:
        raise NotImplementedError

    def list_audit_logs(self, *, tenant_id: str, session_id: Optional[str] = None) -> List[AuditLog]:
        raise NotImplementedError

    def append_event(self, event: EventMessage) -> None:
        raise NotImplementedError

    def list_events(self, *, tenant_id: str) -> List[EventMessage]:
        raise NotImplementedError


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._audit_logs: List[AuditLog] = []
        self._events: List[EventMessage] = []

    def create(self, session: Session) -> Session:
        self._sessions[session.session_id] = session
        return replace(session)

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        return replace(session) if session else None

    def update(self, session: Session) -> Session:
        self._sessions[session.session_id] = session
        return replace(session)

    def list_by_filters(
        self,
        *,
        tenant_id: str,
        status: Optional[str] = None,
        delivery_mode: Optional[str] = None,
        course_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
    ) -> List[Session]:
        sessions = [s for s in self._sessions.values() if s.tenant_id == tenant_id]
        if status:
            sessions = [s for s in sessions if s.status.value == status]
        if delivery_mode:
            sessions = [s for s in sessions if s.delivery_mode.value == delivery_mode]
        if course_id:
            sessions = [s for s in sessions if s.course_id == course_id]
        if cohort_id:
            sessions = [s for s in sessions if cohort_id in s.cohort_ids]
        if instructor_id:
            sessions = [s for s in sessions if instructor_id in s.instructor_refs]
        return [replace(s) for s in sessions]

    def append_audit_log(self, log: AuditLog) -> None:
        self._audit_logs.append(log)

    def list_audit_logs(self, *, tenant_id: str, session_id: Optional[str] = None) -> List[AuditLog]:
        logs = [l for l in self._audit_logs if l.tenant_id == tenant_id]
        if session_id:
            logs = [l for l in logs if l.session_id == session_id]
        return [replace(l) for l in logs]

    def append_event(self, event: EventMessage) -> None:
        self._events.append(event)

    def list_events(self, *, tenant_id: str) -> List[EventMessage]:
        return [replace(e) for e in self._events if e.tenant_id == tenant_id]
