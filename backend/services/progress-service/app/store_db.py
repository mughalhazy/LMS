"""SQLite-backed progress store — persistent implementation of ProgressStore and IdempotencyStore.

Tables (per SPEC_12 §3.1):
  progress_records                  — authoritative lesson/course progress per learner
  course_progress_snapshots         — owned projection: per-learner/course rollup
  learning_path_progress_snapshots  — owned projection: per-learner/path rollup
  completion_metrics_daily          — aggregate daily metrics
  progress_audit_log                — immutable audit trail (append-only)
  idempotency_keys                  — deduplication store for progress event processing

Architecture anchors:
  ARCH_04 — progress-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
  SPEC_12 §2 — progress keyed by (enrollment_id, lesson_id|NULL); tenant_id required.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    CompletionMetricDaily,
    CourseProgressSnapshot,
    LearningPathProgressSnapshot,
    ProgressAuditEntry,
    ProgressRecord,
)


# ──────────────────────────────────────────────────────────────────── #
# Helpers                                                              #
# ──────────────────────────────────────────────────────────────────── #

def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


# ──────────────────────────────────────────────────────────────────── #
# SQLite progress store                                                #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteProgressStore(BaseRepository):
    """Persistent ProgressStore backed by SQLite.

    Implements app.store.ProgressStore Protocol — drop-in for InMemoryProgressStore.
    """

    _SERVICE_NAME = "progress-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                -- SPEC_12 §3.1.1 — authoritative progress records
                CREATE TABLE IF NOT EXISTS progress_records (
                    progress_id          TEXT PRIMARY KEY,
                    tenant_id            TEXT NOT NULL,
                    enrollment_id        TEXT NOT NULL,
                    learner_id           TEXT NOT NULL,
                    course_id            TEXT NOT NULL,
                    lesson_id            TEXT,
                    progress_percentage  REAL NOT NULL DEFAULT 0,
                    status               TEXT NOT NULL DEFAULT 'not_started',
                    last_activity_at     TEXT NOT NULL,
                    completed_at         TEXT,
                    created_at           TEXT NOT NULL,
                    updated_at           TEXT NOT NULL,
                    UNIQUE (tenant_id, enrollment_id, lesson_id)
                );
                CREATE INDEX IF NOT EXISTS idx_progress_learner
                    ON progress_records (tenant_id, learner_id, course_id);

                -- SPEC_12 §3.1.2 — course-level snapshot (upsert pattern)
                CREATE TABLE IF NOT EXISTS course_progress_snapshots (
                    tenant_id                   TEXT NOT NULL,
                    learner_id                  TEXT NOT NULL,
                    course_id                   TEXT NOT NULL,
                    enrollment_id               TEXT NOT NULL,
                    completed_lessons           INTEGER NOT NULL DEFAULT 0,
                    total_lessons               INTEGER NOT NULL DEFAULT 0,
                    progress_percentage         REAL NOT NULL DEFAULT 0,
                    completion_status           TEXT NOT NULL,
                    started_at                  TEXT NOT NULL,
                    completed_at                TEXT,
                    last_activity_at            TEXT NOT NULL,
                    final_score                 REAL,
                    certificate_id              TEXT,
                    total_time_spent_seconds    INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (tenant_id, learner_id, course_id)
                );

                -- Learning-path snapshot (upsert pattern)
                CREATE TABLE IF NOT EXISTS learning_path_progress_snapshots (
                    tenant_id                TEXT NOT NULL,
                    learner_id               TEXT NOT NULL,
                    learning_path_id         TEXT NOT NULL,
                    assigned_course_ids      TEXT NOT NULL DEFAULT '[]',
                    completed_course_ids     TEXT NOT NULL DEFAULT '[]',
                    progress_percentage      REAL NOT NULL DEFAULT 0,
                    current_course_id        TEXT,
                    status                   TEXT NOT NULL DEFAULT 'not_started',
                    expected_completion_date TEXT,
                    last_activity_at         TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, learner_id, learning_path_id)
                );

                -- Daily aggregated completion metrics
                CREATE TABLE IF NOT EXISTS completion_metrics_daily (
                    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id                    TEXT NOT NULL,
                    metric_date                  TEXT NOT NULL,
                    course_id                    TEXT,
                    learning_path_id             TEXT,
                    started_count                INTEGER NOT NULL DEFAULT 0,
                    completed_count              INTEGER NOT NULL DEFAULT 0,
                    completion_rate              REAL NOT NULL DEFAULT 0,
                    avg_time_to_complete_seconds REAL NOT NULL DEFAULT 0,
                    avg_progress_percentage      REAL NOT NULL DEFAULT 0
                );

                -- Immutable progress audit trail
                CREATE TABLE IF NOT EXISTS progress_audit_log (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id        TEXT NOT NULL,
                    actor_id         TEXT NOT NULL,
                    action           TEXT NOT NULL,
                    progress_id      TEXT,
                    idempotency_key  TEXT,
                    timestamp        TEXT NOT NULL,
                    details          TEXT NOT NULL
                );
            """)

    # ---------------------------------------------------------------- #
    # ProgressStore Protocol — progress_records                         #
    # ---------------------------------------------------------------- #

    def get_progress(
        self, tenant_id: str, enrollment_id: str, lesson_id: Optional[str]
    ) -> ProgressRecord | None:
        tid = self._require_tenant_id(tenant_id)
        if lesson_id is None:
            extra = "AND enrollment_id = ? AND lesson_id IS NULL"
            params = (enrollment_id,)
        else:
            extra = "AND enrollment_id = ? AND lesson_id = ?"
            params = (enrollment_id, lesson_id)
        with self._connect() as conn:
            row = self._fetch_one(conn, "progress_records", tid, extra, params)
        return self._row_to_progress(dict(row)) if row else None

    def save_progress(self, record: ProgressRecord) -> None:
        """Upsert — insert or replace on (tenant_id, enrollment_id, lesson_id)."""
        tid = self._require_tenant_id(record.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO progress_records
                   (progress_id, tenant_id, enrollment_id, learner_id, course_id, lesson_id,
                    progress_percentage, status, last_activity_at, completed_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, enrollment_id, lesson_id) DO UPDATE SET
                     progress_percentage = excluded.progress_percentage,
                     status              = excluded.status,
                     last_activity_at    = excluded.last_activity_at,
                     completed_at        = excluded.completed_at,
                     updated_at          = excluded.updated_at""",
                (
                    record.progress_id, tid,
                    record.enrollment_id, record.learner_id, record.course_id, record.lesson_id,
                    record.progress_percentage, record.status,
                    _iso(record.last_activity_at), _iso(record.completed_at),
                    _iso(record.created_at), _iso(record.updated_at),
                ),
            )

    def list_lesson_progress(
        self, tenant_id: str, learner_id: str, course_id: str
    ) -> list[ProgressRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "progress_records", tid,
                "AND learner_id = ? AND course_id = ? AND lesson_id IS NOT NULL",
                (learner_id, course_id),
            )
        return [self._row_to_progress(dict(r)) for r in rows]

    def list_learner_progress(self, tenant_id: str, learner_id: str) -> list[ProgressRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "progress_records", tid,
                "AND learner_id = ?", (learner_id,),
            )
        return [self._row_to_progress(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # ProgressStore Protocol — course_progress_snapshots                #
    # ---------------------------------------------------------------- #

    def save_course_snapshot(self, snapshot: CourseProgressSnapshot) -> None:
        tid = self._require_tenant_id(snapshot.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO course_progress_snapshots
                   (tenant_id, learner_id, course_id, enrollment_id, completed_lessons, total_lessons,
                    progress_percentage, completion_status, started_at, completed_at, last_activity_at,
                    final_score, certificate_id, total_time_spent_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, learner_id, course_id) DO UPDATE SET
                     enrollment_id            = excluded.enrollment_id,
                     completed_lessons        = excluded.completed_lessons,
                     total_lessons            = excluded.total_lessons,
                     progress_percentage      = excluded.progress_percentage,
                     completion_status        = excluded.completion_status,
                     completed_at             = excluded.completed_at,
                     last_activity_at         = excluded.last_activity_at,
                     final_score              = excluded.final_score,
                     certificate_id           = excluded.certificate_id,
                     total_time_spent_seconds = excluded.total_time_spent_seconds""",
                (
                    tid, snapshot.learner_id, snapshot.course_id, snapshot.enrollment_id,
                    snapshot.completed_lessons, snapshot.total_lessons,
                    snapshot.progress_percentage, snapshot.completion_status,
                    _iso(snapshot.started_at), _iso(snapshot.completed_at),
                    _iso(snapshot.last_activity_at),
                    snapshot.final_score, snapshot.certificate_id,
                    snapshot.total_time_spent_seconds,
                ),
            )

    def get_course_snapshot(
        self, tenant_id: str, learner_id: str, course_id: str
    ) -> CourseProgressSnapshot | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "course_progress_snapshots", tid,
                "AND learner_id = ? AND course_id = ?", (learner_id, course_id),
            )
        return self._row_to_course_snapshot(dict(row)) if row else None

    def list_course_snapshots(
        self, tenant_id: str, learner_id: str
    ) -> list[CourseProgressSnapshot]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "course_progress_snapshots", tid,
                "AND learner_id = ?", (learner_id,),
            )
        return [self._row_to_course_snapshot(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # ProgressStore Protocol — learning_path_progress_snapshots         #
    # ---------------------------------------------------------------- #

    def save_path_snapshot(self, snapshot: LearningPathProgressSnapshot) -> None:
        tid = self._require_tenant_id(snapshot.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO learning_path_progress_snapshots
                   (tenant_id, learner_id, learning_path_id, assigned_course_ids, completed_course_ids,
                    progress_percentage, current_course_id, status, expected_completion_date, last_activity_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, learner_id, learning_path_id) DO UPDATE SET
                     assigned_course_ids      = excluded.assigned_course_ids,
                     completed_course_ids     = excluded.completed_course_ids,
                     progress_percentage      = excluded.progress_percentage,
                     current_course_id        = excluded.current_course_id,
                     status                   = excluded.status,
                     expected_completion_date = excluded.expected_completion_date,
                     last_activity_at         = excluded.last_activity_at""",
                (
                    tid, snapshot.learner_id, snapshot.learning_path_id,
                    json.dumps(snapshot.assigned_course_ids),
                    json.dumps(snapshot.completed_course_ids),
                    snapshot.progress_percentage,
                    snapshot.current_course_id,
                    snapshot.status,
                    snapshot.expected_completion_date,
                    _iso(snapshot.last_activity_at),
                ),
            )

    def list_path_snapshots(
        self, tenant_id: str, learner_id: str
    ) -> list[LearningPathProgressSnapshot]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "learning_path_progress_snapshots", tid,
                "AND learner_id = ?", (learner_id,),
            )
        return [self._row_to_path_snapshot(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # ProgressStore Protocol — audit + metrics                          #
    # ---------------------------------------------------------------- #

    def append_audit(self, entry: ProgressAuditEntry) -> None:
        tid = self._require_tenant_id(entry.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO progress_audit_log
                   (tenant_id, actor_id, action, progress_id, idempotency_key, timestamp, details)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid, entry.actor_id, entry.action,
                    entry.progress_id, entry.idempotency_key,
                    _iso(entry.timestamp),
                    json.dumps(entry.details),
                ),
            )

    def save_metric(self, metric: CompletionMetricDaily) -> None:
        tid = self._require_tenant_id(metric.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO completion_metrics_daily
                   (tenant_id, metric_date, course_id, learning_path_id, started_count, completed_count,
                    completion_rate, avg_time_to_complete_seconds, avg_progress_percentage)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid, metric.metric_date, metric.course_id, metric.learning_path_id,
                    metric.started_count, metric.completed_count,
                    metric.completion_rate, metric.avg_time_to_complete_seconds,
                    metric.avg_progress_percentage,
                ),
            )

    # ---------------------------------------------------------------- #
    # Deserialisation helpers                                            #
    # ---------------------------------------------------------------- #

    @staticmethod
    def _row_to_progress(r: dict) -> ProgressRecord:
        return ProgressRecord(
            progress_id=r["progress_id"],
            tenant_id=r["tenant_id"],
            enrollment_id=r["enrollment_id"],
            learner_id=r["learner_id"],
            course_id=r["course_id"],
            lesson_id=r.get("lesson_id"),
            progress_percentage=r["progress_percentage"],
            status=r["status"],
            last_activity_at=datetime.fromisoformat(r["last_activity_at"]),
            completed_at=_dt(r.get("completed_at")),
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
        )

    @staticmethod
    def _row_to_course_snapshot(r: dict) -> CourseProgressSnapshot:
        return CourseProgressSnapshot(
            tenant_id=r["tenant_id"],
            learner_id=r["learner_id"],
            course_id=r["course_id"],
            enrollment_id=r["enrollment_id"],
            completed_lessons=r["completed_lessons"],
            total_lessons=r["total_lessons"],
            progress_percentage=r["progress_percentage"],
            completion_status=r["completion_status"],
            started_at=datetime.fromisoformat(r["started_at"]),
            completed_at=_dt(r.get("completed_at")),
            last_activity_at=datetime.fromisoformat(r["last_activity_at"]),
            final_score=r.get("final_score"),
            certificate_id=r.get("certificate_id"),
            total_time_spent_seconds=r.get("total_time_spent_seconds", 0),
        )

    @staticmethod
    def _row_to_path_snapshot(r: dict) -> LearningPathProgressSnapshot:
        return LearningPathProgressSnapshot(
            tenant_id=r["tenant_id"],
            learner_id=r["learner_id"],
            learning_path_id=r["learning_path_id"],
            assigned_course_ids=json.loads(r["assigned_course_ids"]),
            completed_course_ids=json.loads(r["completed_course_ids"]),
            progress_percentage=r["progress_percentage"],
            current_course_id=r.get("current_course_id"),
            status=r["status"],
            expected_completion_date=r.get("expected_completion_date"),
            last_activity_at=datetime.fromisoformat(r["last_activity_at"]),
        )


class SQLiteIdempotencyStore(BaseRepository):
    """Persistent IdempotencyStore backed by SQLite.

    Implements app.store.IdempotencyStore Protocol — drop-in for InMemoryIdempotencyStore.
    Prevents duplicate progress event processing via (tenant_id, idempotency_key) uniqueness.
    """

    _SERVICE_NAME = "progress-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    tenant_id TEXT NOT NULL,
                    ikey      TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, ikey)
                )
            """)

    def seen(self, tenant_id: str, key: str) -> bool:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM idempotency_keys WHERE tenant_id = ? AND ikey = ? LIMIT 1",
                (tid, key),
            ).fetchone()
        return row is not None

    def remember(self, tenant_id: str, key: str) -> None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO idempotency_keys (tenant_id, ikey) VALUES (?, ?)",
                (tid, key),
            )
