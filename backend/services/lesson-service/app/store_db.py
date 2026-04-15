"""SQLite-backed lesson store — persistent implementation of LessonStore ABC.

Tables:
  lessons             — Lesson domain object (tenant-scoped)
  lesson_audit_log    — AuditRecord (append-only, tenant-scoped)
  lesson_outbox_events — OutboxEvent (append-only, tenant-scoped)

Architecture anchors:
  ARCH_04 — lesson-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import AuditRecord, LifecycleAction, Lesson, LessonStatus, OutboxEvent
from .store import LessonStore


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SQLiteLessonStore(LessonStore, BaseRepository):
    """Persistent LessonStore backed by SQLite.

    Extends LessonStore ABC and BaseRepository mixin — drop-in for InMemoryLessonStore.
    """

    _SERVICE_NAME = "lesson-service"

    def __init__(self, db_path: Path | None = None) -> None:
        BaseRepository.__init__(self, db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id                   TEXT NOT NULL,
                    tenant_id                   TEXT NOT NULL,
                    course_id                   TEXT NOT NULL,
                    title                       TEXT NOT NULL,
                    created_by                  TEXT NOT NULL,
                    lesson_type                 TEXT NOT NULL DEFAULT 'self_paced',
                    description                 TEXT,
                    module_id                   TEXT,
                    learning_objectives         TEXT NOT NULL DEFAULT '[]',
                    content_ref                 TEXT,
                    estimated_duration_minutes  INTEGER,
                    availability_rules          TEXT NOT NULL DEFAULT '{}',
                    metadata                    TEXT NOT NULL DEFAULT '{}',
                    delivery_state              TEXT NOT NULL DEFAULT '{}',
                    order_index                 INTEGER NOT NULL DEFAULT 0,
                    version                     INTEGER NOT NULL DEFAULT 1,
                    published_version           INTEGER,
                    status                      TEXT NOT NULL DEFAULT 'draft',
                    published_at                TEXT,
                    archived_at                 TEXT,
                    created_at                  TEXT NOT NULL,
                    updated_at                  TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, lesson_id)
                );
                CREATE INDEX IF NOT EXISTS idx_lessons_course
                    ON lessons (tenant_id, course_id, order_index, created_at);

                CREATE TABLE IF NOT EXISTS lesson_audit_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id   TEXT NOT NULL,
                    lesson_id   TEXT NOT NULL,
                    actor_id    TEXT NOT NULL,
                    action      TEXT NOT NULL,
                    detail      TEXT NOT NULL DEFAULT '{}',
                    created_at  TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lesson_audit_lesson
                    ON lesson_audit_log (tenant_id, lesson_id);

                CREATE TABLE IF NOT EXISTS lesson_outbox_events (
                    event_id        TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    event_type      TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,
                    correlation_id  TEXT NOT NULL,
                    payload         TEXT NOT NULL DEFAULT '{}',
                    metadata        TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (tenant_id, event_id)
                );
            """)

    # ---------------------------------------------------------------- #
    # LessonStore ABC — core CRUD                                       #
    # ---------------------------------------------------------------- #

    def create(self, lesson: Lesson) -> Lesson:
        tid = self._require_tenant_id(lesson.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO lessons
                   (lesson_id, tenant_id, course_id, title, created_by, lesson_type,
                    description, module_id, learning_objectives, content_ref,
                    estimated_duration_minutes, availability_rules, metadata,
                    delivery_state, order_index, version, published_version,
                    status, published_at, archived_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    lesson.lesson_id, tid, lesson.course_id, lesson.title, lesson.created_by,
                    lesson.lesson_type, lesson.description, lesson.module_id,
                    json.dumps(lesson.learning_objectives), lesson.content_ref,
                    lesson.estimated_duration_minutes,
                    json.dumps(lesson.availability_rules), json.dumps(lesson.metadata),
                    json.dumps(lesson.delivery_state), lesson.order_index,
                    lesson.version, lesson.published_version,
                    lesson.status.value,
                    _iso(lesson.published_at), _iso(lesson.archived_at),
                    _iso(lesson.created_at), _iso(lesson.updated_at),
                ),
            )
        return lesson

    def get(self, tenant_id: str, lesson_id: str) -> Lesson | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(conn, "lessons", tid, "AND lesson_id = ?", (lesson_id,))
        return _row_to_lesson(dict(row)) if row else None

    def list(self, tenant_id: str, course_id: str | None = None) -> list[Lesson]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            if course_id:
                rows = self._fetch_all(
                    conn, "lessons", tid,
                    "AND course_id = ?", (course_id,),
                    order_by="course_id ASC, order_index ASC, created_at ASC",
                )
            else:
                rows = self._fetch_all(
                    conn, "lessons", tid,
                    order_by="course_id ASC, order_index ASC, created_at ASC",
                )
        return [_row_to_lesson(dict(r)) for r in rows]

    def update(self, lesson: Lesson) -> Lesson:
        tid = self._require_tenant_id(lesson.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE lessons SET
                   title = ?, lesson_type = ?, description = ?, module_id = ?,
                   learning_objectives = ?, content_ref = ?,
                   estimated_duration_minutes = ?, availability_rules = ?,
                   metadata = ?, delivery_state = ?, order_index = ?,
                   version = ?, published_version = ?, status = ?,
                   published_at = ?, archived_at = ?, updated_at = ?
                   WHERE tenant_id = ? AND lesson_id = ?""",
                (
                    lesson.title, lesson.lesson_type, lesson.description, lesson.module_id,
                    json.dumps(lesson.learning_objectives), lesson.content_ref,
                    lesson.estimated_duration_minutes,
                    json.dumps(lesson.availability_rules), json.dumps(lesson.metadata),
                    json.dumps(lesson.delivery_state), lesson.order_index,
                    lesson.version, lesson.published_version, lesson.status.value,
                    _iso(lesson.published_at), _iso(lesson.archived_at),
                    _iso(lesson.updated_at),
                    tid, lesson.lesson_id,
                ),
            )
        return lesson

    def delete(self, tenant_id: str, lesson_id: str) -> None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM lessons WHERE tenant_id = ? AND lesson_id = ?",
                (tid, lesson_id),
            )

    # ---------------------------------------------------------------- #
    # LessonStore ABC — audit + outbox                                  #
    # ---------------------------------------------------------------- #

    def append_audit(self, record: AuditRecord) -> None:
        tid = self._require_tenant_id(record.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO lesson_audit_log
                   (tenant_id, lesson_id, actor_id, action, detail, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    tid, record.lesson_id, record.actor_id,
                    record.action.value, json.dumps(record.detail),
                    _iso(record.created_at),
                ),
            )

    def append_event(self, event: OutboxEvent) -> None:
        tid = self._require_tenant_id(event.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO lesson_outbox_events
                   (event_id, tenant_id, event_type, timestamp, correlation_id, payload, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id, tid, event.event_type,
                    _iso(event.timestamp), event.correlation_id,
                    json.dumps(event.payload), json.dumps(event.metadata),
                ),
            )


# ---------------------------------------------------------------- #
# Deserialisation helper                                            #
# ---------------------------------------------------------------- #

def _row_to_lesson(r: dict) -> Lesson:
    return Lesson(
        lesson_id=r["lesson_id"],
        tenant_id=r["tenant_id"],
        course_id=r["course_id"],
        title=r["title"],
        created_by=r["created_by"],
        lesson_type=r["lesson_type"],
        description=r.get("description"),
        module_id=r.get("module_id"),
        learning_objectives=json.loads(r["learning_objectives"]),
        content_ref=r.get("content_ref"),
        estimated_duration_minutes=r.get("estimated_duration_minutes"),
        availability_rules=json.loads(r["availability_rules"]),
        metadata=json.loads(r["metadata"]),
        delivery_state=json.loads(r["delivery_state"]),
        order_index=r["order_index"],
        version=r["version"],
        published_version=r.get("published_version"),
        status=LessonStatus(r["status"]),
        published_at=_dt(r.get("published_at")),
        archived_at=_dt(r.get("archived_at")),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )
