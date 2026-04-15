"""SQLite-backed session repository — persistent implementation of SessionRepository.

Category B: SessionRepository in src/repository.py is an abstract base class (not a Protocol).
SQLiteSessionRepository extends it with a full SQLite implementation.

Tables:
  sessions           — Session dataclass (complex nested structures as JSON)
  session_audit_logs — AuditLog (append-only)
  session_events     — EventMessage outbox

Architecture anchors:
  ARCH_04 — session-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.services.shared.db import BaseRepository, resolve_db_path
from src.repository import SessionRepository
from src.models import AuditLog, DeliveryMetadata, DeliveryMode, EventMessage, RescheduleRecord, Session, SessionSchedule, SessionStatus


# ──────────────────────────────────────────────────────────────────── #
# Serialisation helpers for nested dataclass models                   #
# ──────────────────────────────────────────────────────────────────── #

def _default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):      # Enum
        return obj.value
    raise TypeError(f"Not JSON serialisable: {type(obj)}")


def _session_to_json(session: Session) -> str:
    return json.dumps(asdict(session), default=_default)


def _json_to_session(data: str) -> Session:
    d = json.loads(data)

    schedule = None
    if d.get("schedule"):
        s = d["schedule"]
        schedule = SessionSchedule(
            timezone=s["timezone"],
            start_at=datetime.fromisoformat(s["start_at"]),
            end_at=datetime.fromisoformat(s["end_at"]),
            recurrence_rule=s.get("recurrence_rule"),
        )

    reschedule_history = [
        RescheduleRecord(
            previous_start_at=datetime.fromisoformat(r["previous_start_at"]),
            previous_end_at=datetime.fromisoformat(r["previous_end_at"]),
            new_start_at=datetime.fromisoformat(r["new_start_at"]),
            new_end_at=datetime.fromisoformat(r["new_end_at"]),
            actor_id=r["actor_id"],
            reason=r["reason"],
            changed_at=datetime.fromisoformat(r["changed_at"]),
        )
        for r in d.get("reschedule_history", [])
    ]

    dm = d.get("delivery_metadata", {})
    delivery_metadata = DeliveryMetadata(
        join_instructions=dm.get("join_instructions"),
        recording_policy=dm.get("recording_policy", "optional"),
        location=dm.get("location", {}),
        online_provider=dm.get("online_provider"),
        online_join_url=dm.get("online_join_url"),
        online_host_url=dm.get("online_host_url"),
        dial_in_info=dm.get("dial_in_info"),
        hybrid_attendance_policy=dm.get("hybrid_attendance_policy"),
    )

    return Session(
        session_id=d["session_id"],
        tenant_id=d["tenant_id"],
        status=SessionStatus(d["status"]),
        title=d["title"],
        description=d.get("description"),
        course_id=d["course_id"],
        lesson_id=d.get("lesson_id"),
        cohort_ids=d.get("cohort_ids", []),
        delivery_mode=DeliveryMode(d["delivery_mode"]),
        instructor_refs=d.get("instructor_refs", []),
        capacity=d.get("capacity"),
        waitlist_enabled=d.get("waitlist_enabled", False),
        delivery_metadata=delivery_metadata,
        schedule=schedule,
        reschedule_history=reschedule_history,
        created_by=d.get("created_by", "system"),
        updated_by=d.get("updated_by", "system"),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
        actual_start_at=datetime.fromisoformat(d["actual_start_at"]) if d.get("actual_start_at") else None,
        actual_end_at=datetime.fromisoformat(d["actual_end_at"]) if d.get("actual_end_at") else None,
        version=d.get("version", 1),
    )


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


# ──────────────────────────────────────────────────────────────────── #
# SQLite repository                                                    #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteSessionRepository(SessionRepository, BaseRepository):
    """Persistent SessionRepository backed by SQLite.

    Extends src.repository.SessionRepository (abstract base class) with SQLite persistence.
    Drop-in replacement for InMemorySessionRepository.
    """

    _SERVICE_NAME = "session-service"

    def __init__(self, db_path: Path | None = None) -> None:
        # BaseRepository.__init__ calls _init_schema
        BaseRepository.__init__(self, db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id    TEXT PRIMARY KEY,
                    tenant_id     TEXT NOT NULL,
                    status        TEXT NOT NULL,
                    course_id     TEXT NOT NULL,
                    delivery_mode TEXT NOT NULL,
                    version       INTEGER NOT NULL DEFAULT 1,
                    created_at    TEXT NOT NULL,
                    updated_at    TEXT NOT NULL,
                    data          TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_tenant_status
                    ON sessions (tenant_id, status);
                CREATE INDEX IF NOT EXISTS idx_sessions_tenant_course
                    ON sessions (tenant_id, course_id);

                CREATE TABLE IF NOT EXISTS session_audit_logs (
                    audit_id   TEXT PRIMARY KEY,
                    tenant_id  TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    action     TEXT NOT NULL,
                    actor_id   TEXT NOT NULL,
                    details    TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS session_events (
                    event_id       TEXT PRIMARY KEY,
                    event_type     TEXT NOT NULL,
                    timestamp      TEXT NOT NULL,
                    tenant_id      TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    payload        TEXT NOT NULL,
                    metadata       TEXT NOT NULL DEFAULT '{}'
                );
            """)

    # ---------------------------------------------------------------- #
    # SessionRepository — session CRUD                                  #
    # ---------------------------------------------------------------- #

    def create(self, session: Session) -> Session:
        tid = self._require_tenant_id(session.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO sessions
                   (session_id, tenant_id, status, course_id, delivery_mode, version, created_at, updated_at, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session.session_id, tid,
                    session.status.value, session.course_id,
                    session.delivery_mode.value, session.version,
                    _iso(session.created_at), _iso(session.updated_at),
                    _session_to_json(session),
                ),
            )
        return session

    def get(self, session_id: str) -> Optional[Session]:
        # session_id is globally unique — direct lookup without tenant filter
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM sessions WHERE session_id = ? LIMIT 1",
                (session_id,),
            ).fetchone()
        return _json_to_session(row["data"]) if row else None

    def update(self, session: Session) -> Session:
        tid = self._require_tenant_id(session.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE sessions
                   SET status = ?, delivery_mode = ?, version = ?, updated_at = ?, data = ?
                   WHERE tenant_id = ? AND session_id = ?""",
                (
                    session.status.value, session.delivery_mode.value,
                    session.version, _iso(session.updated_at),
                    _session_to_json(session),
                    tid, session.session_id,
                ),
            )
        return session

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
        """Filter sessions by tenant + optional predicates.

        cohort_id and instructor_id are stored inside the JSON `data` column — these are
        filtered in Python after DB retrieval (acceptable for service-level list ops).
        """
        tid = self._require_tenant_id(tenant_id)
        extra = ""
        params: list = []
        if status:
            extra += " AND status = ?"
            params.append(status)
        if delivery_mode:
            extra += " AND delivery_mode = ?"
            params.append(delivery_mode)
        if course_id:
            extra += " AND course_id = ?"
            params.append(course_id)

        with self._connect() as conn:
            rows = self._fetch_all(conn, "sessions", tid, extra, tuple(params))

        sessions = [_json_to_session(r["data"]) for r in rows]

        # In-Python filters for list-typed fields (cohort_ids, instructor_refs)
        if cohort_id:
            sessions = [s for s in sessions if cohort_id in s.cohort_ids]
        if instructor_id:
            sessions = [s for s in sessions if instructor_id in s.instructor_refs]
        return sessions

    # ---------------------------------------------------------------- #
    # SessionRepository — audit logs                                    #
    # ---------------------------------------------------------------- #

    def append_audit_log(self, log: AuditLog) -> None:
        tid = self._require_tenant_id(log.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO session_audit_logs
                   (audit_id, tenant_id, session_id, action, actor_id, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    log.audit_id, tid, log.session_id,
                    log.action, log.actor_id,
                    json.dumps(log.details, default=_default),
                    _iso(log.created_at),
                ),
            )

    def list_audit_logs(
        self, *, tenant_id: str, session_id: Optional[str] = None
    ) -> List[AuditLog]:
        tid = self._require_tenant_id(tenant_id)
        extra = ""
        params: tuple = ()
        if session_id:
            extra = "AND session_id = ?"
            params = (session_id,)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "session_audit_logs", tid, extra, params, order_by="created_at ASC"
            )
        return [
            AuditLog(
                audit_id=r["audit_id"],
                tenant_id=r["tenant_id"],
                session_id=r["session_id"],
                action=r["action"],
                actor_id=r["actor_id"],
                details=json.loads(r["details"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # ---------------------------------------------------------------- #
    # SessionRepository — events (outbox)                              #
    # ---------------------------------------------------------------- #

    def append_event(self, event: EventMessage) -> None:
        tid = self._require_tenant_id(event.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO session_events
                   (event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id, event.event_type,
                    _iso(event.timestamp), tid,
                    event.correlation_id,
                    json.dumps(event.payload, default=_default),
                    json.dumps(event.metadata, default=_default),
                ),
            )

    def list_events(self, *, tenant_id: str) -> List[EventMessage]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "session_events", tid, order_by="timestamp ASC"
            )
        return [
            EventMessage(
                event_id=r["event_id"],
                event_type=r["event_type"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                tenant_id=r["tenant_id"],
                correlation_id=r["correlation_id"],
                payload=json.loads(r["payload"]),
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]
