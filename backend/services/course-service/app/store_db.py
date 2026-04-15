"""SQLite-backed course store — persistent implementation of CourseStorageContract Protocol.

Tables:
  courses — CourseRecord (tenant-scoped; metadata/program_links/session_links as JSON)

Architecture anchors:
  ARCH_04 — course-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL; tenant-first list queries.

Note: CourseStorageContract.get(course_id) has no tenant_id parameter — matches Protocol as-is.
      list_by_tenant enforces tenant isolation at the list boundary.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .service import CourseRecord, CourseStorageContract
from .schemas import CourseMetadata, CourseStatus, ProgramLink, PublishStatus, SessionLink


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SQLiteCourseStorage(BaseRepository):
    """Persistent CourseStorageContract backed by SQLite.

    Implements CourseStorageContract Protocol — drop-in for InMemoryCourseStorage.
    """

    _SERVICE_NAME = "course-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id           TEXT PRIMARY KEY NOT NULL,
                    tenant_id           TEXT NOT NULL,
                    institution_id      TEXT,
                    created_at          TEXT NOT NULL,
                    updated_at          TEXT NOT NULL,
                    status              TEXT NOT NULL DEFAULT 'draft',
                    publish_status      TEXT NOT NULL DEFAULT 'unpublished',
                    published_at        TEXT,
                    published_by        TEXT,
                    created_by          TEXT NOT NULL,
                    course_code         TEXT,
                    title               TEXT NOT NULL,
                    description         TEXT,
                    language_code       TEXT,
                    credit_value        REAL,
                    grading_scheme      TEXT,
                    metadata            TEXT NOT NULL DEFAULT '{}',
                    program_links       TEXT NOT NULL DEFAULT '[]',
                    session_links       TEXT NOT NULL DEFAULT '[]'
                );
                CREATE INDEX IF NOT EXISTS idx_courses_tenant
                    ON courses (tenant_id);
            """)

    # ---------------------------------------------------------------- #
    # CourseStorageContract Protocol                                    #
    # ---------------------------------------------------------------- #

    def save(self, record: CourseRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO courses
                   (course_id, tenant_id, institution_id, created_at, updated_at,
                    status, publish_status, published_at, published_by, created_by,
                    course_code, title, description, language_code, credit_value,
                    grading_scheme, metadata, program_links, session_links)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(course_id) DO UPDATE SET
                       tenant_id = excluded.tenant_id,
                       institution_id = excluded.institution_id,
                       updated_at = excluded.updated_at,
                       status = excluded.status,
                       publish_status = excluded.publish_status,
                       published_at = excluded.published_at,
                       published_by = excluded.published_by,
                       course_code = excluded.course_code,
                       title = excluded.title,
                       description = excluded.description,
                       language_code = excluded.language_code,
                       credit_value = excluded.credit_value,
                       grading_scheme = excluded.grading_scheme,
                       metadata = excluded.metadata,
                       program_links = excluded.program_links,
                       session_links = excluded.session_links""",
                (
                    record.course_id, record.tenant_id, record.institution_id,
                    _iso(record.created_at), _iso(record.updated_at),
                    record.status.value, record.publish_status.value,
                    _iso(record.published_at), record.published_by, record.created_by,
                    record.course_code, record.title, record.description,
                    record.language_code, record.credit_value, record.grading_scheme,
                    record.metadata.model_dump_json(),
                    json.dumps([pl.model_dump(mode="json") for pl in record.program_links]),
                    json.dumps([sl.model_dump(mode="json") for sl in record.session_links]),
                ),
            )

    def get(self, course_id: str) -> CourseRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM courses WHERE course_id = ? LIMIT 1", (course_id,)
            ).fetchone()
        return _row_to_course(dict(row)) if row else None

    def delete(self, course_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))

    def list_by_tenant(self, tenant_id: str) -> list[CourseRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM courses WHERE tenant_id = ? ORDER BY created_at ASC",
                (tid,),
            ).fetchall()
        return [_row_to_course(dict(r)) for r in rows]


# ---------------------------------------------------------------- #
# Deserialisation helper                                            #
# ---------------------------------------------------------------- #

def _row_to_course(r: dict) -> CourseRecord:
    return CourseRecord(
        course_id=r["course_id"],
        tenant_id=r["tenant_id"],
        institution_id=r.get("institution_id"),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
        status=CourseStatus(r["status"]),
        publish_status=PublishStatus(r["publish_status"]),
        published_at=_dt(r.get("published_at")),
        published_by=r.get("published_by"),
        created_by=r["created_by"],
        course_code=r.get("course_code"),
        title=r["title"],
        description=r.get("description"),
        language_code=r.get("language_code"),
        credit_value=r.get("credit_value"),
        grading_scheme=r.get("grading_scheme"),
        metadata=CourseMetadata.model_validate_json(r["metadata"]),
        program_links=[ProgramLink.model_validate(pl) for pl in json.loads(r["program_links"])],
        session_links=[SessionLink.model_validate(sl) for sl in json.loads(r["session_links"])],
    )
