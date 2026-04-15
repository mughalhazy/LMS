"""SQLite-backed enrollment store — persistent implementation of EnrollmentStore and AuditLogStore Protocols.

Tables (per SPEC_11 §3):
  enrollments          — Enrollment dataclass, tenant-scoped
  enrollment_audit_log — AuditLogEntry (append-only)

Architecture anchors:
  ARCH_04 — enrollment-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL; tenant-first query pattern.
  SPEC_11 §3.1 — enrollment_id PK, all SPEC_11 status transition fields preserved.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import AuditLogEntry, Enrollment, EnrollmentStatus


# ──────────────────────────────────────────────────────────────────── #
# Serialisation helpers                                                #
# ──────────────────────────────────────────────────────────────────── #

def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _row_to_enrollment(row: dict) -> Enrollment:
    return Enrollment(
        id=row["id"],
        tenant_id=row["tenant_id"],
        learner_id=row["learner_id"],
        course_id=row["course_id"],
        assigned_by=row["assigned_by"],
        assignment_source=row["assignment_source"],
        cohort_id=row.get("cohort_id"),
        session_id=row.get("session_id"),
        status=EnrollmentStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


# ──────────────────────────────────────────────────────────────────── #
# Store                                                                #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteEnrollmentStore(BaseRepository):
    """Persistent EnrollmentStore backed by SQLite.

    Implements app.store.EnrollmentStore Protocol — drop-in for InMemoryEnrollmentStore.
    """

    _SERVICE_NAME = "enrollment-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id                TEXT PRIMARY KEY,
                    tenant_id         TEXT NOT NULL,
                    learner_id        TEXT NOT NULL,
                    course_id         TEXT NOT NULL,
                    assigned_by       TEXT NOT NULL,
                    assignment_source TEXT NOT NULL,
                    cohort_id         TEXT,
                    session_id        TEXT,
                    status            TEXT NOT NULL DEFAULT 'assigned',
                    created_at        TEXT NOT NULL,
                    updated_at        TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_enroll_learner
                    ON enrollments (tenant_id, learner_id);
                CREATE INDEX IF NOT EXISTS idx_enroll_course
                    ON enrollments (tenant_id, course_id);
                CREATE INDEX IF NOT EXISTS idx_enroll_status
                    ON enrollments (tenant_id, status);

                CREATE TABLE IF NOT EXISTS enrollment_audit_log (
                    rowid_        INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id     TEXT NOT NULL,
                    actor_id      TEXT NOT NULL,
                    action        TEXT NOT NULL,
                    enrollment_id TEXT NOT NULL,
                    metadata      TEXT NOT NULL,
                    created_at    TEXT NOT NULL
                );
            """)

    # ---------------------------------------------------------------- #
    # EnrollmentStore Protocol                                           #
    # ---------------------------------------------------------------- #

    def create(self, enrollment: Enrollment) -> Enrollment:
        tid = self._require_tenant_id(enrollment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO enrollments
                   (id, tenant_id, learner_id, course_id, assigned_by, assignment_source,
                    cohort_id, session_id, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    enrollment.id, tid,
                    enrollment.learner_id, enrollment.course_id,
                    enrollment.assigned_by, enrollment.assignment_source,
                    enrollment.cohort_id, enrollment.session_id,
                    enrollment.status.value,
                    _iso(enrollment.created_at), _iso(enrollment.updated_at),
                ),
            )
        return enrollment

    def get(self, tenant_id: str, enrollment_id: str) -> Enrollment | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(conn, "enrollments", tid, "AND id = ?", (enrollment_id,))
        return _row_to_enrollment(dict(row)) if row else None

    def list(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        course_id: str | None = None,
        status: str | None = None,
    ) -> list[Enrollment]:
        tid = self._require_tenant_id(tenant_id)
        extra = ""
        params: list = []
        if learner_id:
            extra += " AND learner_id = ?"
            params.append(learner_id)
        if course_id:
            extra += " AND course_id = ?"
            params.append(course_id)
        if status:
            extra += " AND status = ?"
            params.append(status)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "enrollments", tid, extra, tuple(params), order_by="created_at ASC"
            )
        return [_row_to_enrollment(dict(r)) for r in rows]

    def update(self, enrollment: Enrollment) -> Enrollment:
        tid = self._require_tenant_id(enrollment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE enrollments
                   SET status = ?, cohort_id = ?, session_id = ?, updated_at = ?
                   WHERE tenant_id = ? AND id = ?""",
                (
                    enrollment.status.value,
                    enrollment.cohort_id, enrollment.session_id,
                    _iso(enrollment.updated_at),
                    tid, enrollment.id,
                ),
            )
        return enrollment

    def active_for_learner_course(
        self, tenant_id: str, learner_id: str, course_id: str
    ) -> Enrollment | None:
        """Return the active/assigned enrollment for a learner-course pair, if any."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "enrollments", tid,
                "AND learner_id = ? AND course_id = ? AND status IN ('assigned','active')",
                (learner_id, course_id),
            )
        return _row_to_enrollment(dict(row)) if row else None

    # ---------------------------------------------------------------- #
    # AuditLogStore Protocol                                             #
    # ---------------------------------------------------------------- #

    def append(self, entry: AuditLogEntry) -> None:
        tid = self._require_tenant_id(entry.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO enrollment_audit_log
                   (tenant_id, actor_id, action, enrollment_id, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    tid, entry.actor_id, entry.action,
                    entry.enrollment_id,
                    json.dumps(entry.metadata),
                    _iso(entry.created_at),
                ),
            )

    def list_audit(self, tenant_id: str) -> list[AuditLogEntry]:
        """Return all audit entries for a tenant (Protocol name: list)."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "enrollment_audit_log", tid, order_by="created_at ASC"
            )
        return [
            AuditLogEntry(
                tenant_id=r["tenant_id"],
                actor_id=r["actor_id"],
                action=r["action"],
                enrollment_id=r["enrollment_id"],
                metadata=json.loads(r["metadata"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]
