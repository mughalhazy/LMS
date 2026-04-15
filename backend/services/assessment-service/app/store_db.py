"""SQLite-backed assessment store — persistent implementation of AssessmentStore Protocol.

Tables:
  assessments  — AssessmentDefinition (assessment catalog, tenant-scoped)
  attempts     — AttemptRecord (per-learner attempt, tenant-scoped)
  submissions  — SubmissionRecord (append-only per attempt, tenant-scoped)

Architecture anchors:
  ARCH_04 — assessment-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import AssessmentDefinition, AssessmentStatus, AssessmentType, AttemptRecord, AttemptStatus, SubmissionRecord


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SQLiteAssessmentStore(BaseRepository):
    """Persistent AssessmentStore backed by SQLite.

    Implements app.store.AssessmentStore Protocol — drop-in for InMemoryAssessmentStore.
    """

    _SERVICE_NAME = "assessment-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id       TEXT NOT NULL,
                    tenant_id           TEXT NOT NULL,
                    course_id           TEXT NOT NULL,
                    lesson_id           TEXT,
                    title               TEXT NOT NULL,
                    description         TEXT,
                    assessment_type     TEXT NOT NULL,
                    status              TEXT NOT NULL DEFAULT 'draft',
                    max_score           REAL NOT NULL DEFAULT 100,
                    passing_score       REAL NOT NULL DEFAULT 60,
                    time_limit_minutes  INTEGER,
                    question_count      INTEGER NOT NULL DEFAULT 0,
                    metadata            TEXT NOT NULL DEFAULT '{}',
                    created_by          TEXT NOT NULL,
                    created_at          TEXT NOT NULL,
                    updated_at          TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, assessment_id)
                );
                CREATE INDEX IF NOT EXISTS idx_assessments_course
                    ON assessments (tenant_id, course_id);

                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id          TEXT NOT NULL,
                    tenant_id           TEXT NOT NULL,
                    assessment_id       TEXT NOT NULL,
                    learner_id          TEXT NOT NULL,
                    status              TEXT NOT NULL DEFAULT 'started',
                    started_at          TEXT NOT NULL,
                    submitted_at        TEXT,
                    grading_result_id   TEXT,
                    exam_session_id     TEXT,
                    isolation_key       TEXT,
                    PRIMARY KEY (tenant_id, attempt_id)
                );
                CREATE INDEX IF NOT EXISTS idx_attempts_assessment
                    ON attempts (tenant_id, assessment_id);

                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id   TEXT NOT NULL,
                    attempt_id      TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    payload         TEXT NOT NULL,
                    submitted_by    TEXT NOT NULL,
                    submitted_at    TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, submission_id)
                );
                CREATE INDEX IF NOT EXISTS idx_submissions_attempt
                    ON submissions (tenant_id, attempt_id);
            """)

    # ---------------------------------------------------------------- #
    # AssessmentStore Protocol — definitions                            #
    # ---------------------------------------------------------------- #

    def create_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition:
        tid = self._require_tenant_id(assessment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO assessments
                   (assessment_id, tenant_id, course_id, lesson_id, title, description,
                    assessment_type, status, max_score, passing_score, time_limit_minutes,
                    question_count, metadata, created_by, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    assessment.assessment_id, tid,
                    assessment.course_id, assessment.lesson_id,
                    assessment.title, assessment.description,
                    assessment.assessment_type.value,
                    assessment.status.value,
                    assessment.max_score, assessment.passing_score,
                    assessment.time_limit_minutes, assessment.question_count,
                    json.dumps(assessment.metadata),
                    assessment.created_by,
                    _iso(assessment.created_at), _iso(assessment.updated_at),
                ),
            )
        return assessment

    def get_assessment(self, tenant_id: str, assessment_id: str) -> AssessmentDefinition | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "assessments", tid, "AND assessment_id = ?", (assessment_id,)
            )
        return self._row_to_assessment(dict(row)) if row else None

    def list_assessments(self, tenant_id: str) -> list[AssessmentDefinition]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "assessments", tid, order_by="created_at ASC")
        return [self._row_to_assessment(dict(r)) for r in rows]

    def update_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition:
        tid = self._require_tenant_id(assessment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE assessments SET
                   title = ?, description = ?, status = ?, max_score = ?,
                   passing_score = ?, time_limit_minutes = ?, question_count = ?,
                   metadata = ?, updated_at = ?
                   WHERE tenant_id = ? AND assessment_id = ?""",
                (
                    assessment.title, assessment.description,
                    assessment.status.value,
                    assessment.max_score, assessment.passing_score,
                    assessment.time_limit_minutes, assessment.question_count,
                    json.dumps(assessment.metadata),
                    _iso(assessment.updated_at),
                    tid, assessment.assessment_id,
                ),
            )
        return assessment

    def delete_assessment(self, tenant_id: str, assessment_id: str) -> None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM assessments WHERE tenant_id = ? AND assessment_id = ?",
                (tid, assessment_id),
            )

    # ---------------------------------------------------------------- #
    # AssessmentStore Protocol — attempts                               #
    # ---------------------------------------------------------------- #

    def create_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        tid = self._require_tenant_id(attempt.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO attempts
                   (attempt_id, tenant_id, assessment_id, learner_id, status,
                    started_at, submitted_at, grading_result_id, exam_session_id, isolation_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    attempt.attempt_id, tid,
                    attempt.assessment_id, attempt.learner_id,
                    attempt.status.value,
                    _iso(attempt.started_at), _iso(attempt.submitted_at),
                    attempt.grading_result_id, attempt.exam_session_id, attempt.isolation_key,
                ),
            )
        return attempt

    def get_attempt(self, tenant_id: str, attempt_id: str) -> AttemptRecord | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "attempts", tid, "AND attempt_id = ?", (attempt_id,)
            )
        return self._row_to_attempt(dict(row)) if row else None

    def list_attempts(self, tenant_id: str, assessment_id: str) -> list[AttemptRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "attempts", tid,
                "AND assessment_id = ?", (assessment_id,),
                order_by="started_at ASC",
            )
        return [self._row_to_attempt(dict(r)) for r in rows]

    def update_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        tid = self._require_tenant_id(attempt.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE attempts SET
                   status = ?, submitted_at = ?, grading_result_id = ?
                   WHERE tenant_id = ? AND attempt_id = ?""",
                (
                    attempt.status.value, _iso(attempt.submitted_at),
                    attempt.grading_result_id,
                    tid, attempt.attempt_id,
                ),
            )
        return attempt

    # ---------------------------------------------------------------- #
    # AssessmentStore Protocol — submissions                            #
    # ---------------------------------------------------------------- #

    def save_submission(self, submission: SubmissionRecord) -> SubmissionRecord:
        tid = self._require_tenant_id(submission.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO submissions
                   (submission_id, attempt_id, tenant_id, payload, submitted_by, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    submission.submission_id, submission.attempt_id, tid,
                    json.dumps(submission.payload),
                    submission.submitted_by, _iso(submission.submitted_at),
                ),
            )
        return submission

    def list_submissions(self, tenant_id: str, attempt_id: str) -> list[SubmissionRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "submissions", tid,
                "AND attempt_id = ?", (attempt_id,),
                order_by="submitted_at ASC",
            )
        return [
            SubmissionRecord(
                submission_id=r["submission_id"],
                attempt_id=r["attempt_id"],
                tenant_id=r["tenant_id"],
                payload=json.loads(r["payload"]),
                submitted_by=r["submitted_by"],
                submitted_at=datetime.fromisoformat(r["submitted_at"]),
            )
            for r in rows
        ]

    # ---------------------------------------------------------------- #
    # Deserialisation helpers                                            #
    # ---------------------------------------------------------------- #

    @staticmethod
    def _row_to_assessment(r: dict) -> AssessmentDefinition:
        return AssessmentDefinition(
            assessment_id=r["assessment_id"],
            tenant_id=r["tenant_id"],
            course_id=r["course_id"],
            lesson_id=r.get("lesson_id"),
            title=r["title"],
            description=r.get("description"),
            assessment_type=AssessmentType(r["assessment_type"]),
            status=AssessmentStatus(r["status"]),
            max_score=r["max_score"],
            passing_score=r["passing_score"],
            time_limit_minutes=r.get("time_limit_minutes"),
            question_count=r["question_count"],
            metadata=json.loads(r["metadata"]),
            created_by=r["created_by"],
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
        )

    @staticmethod
    def _row_to_attempt(r: dict) -> AttemptRecord:
        return AttemptRecord(
            attempt_id=r["attempt_id"],
            tenant_id=r["tenant_id"],
            assessment_id=r["assessment_id"],
            learner_id=r["learner_id"],
            started_at=datetime.fromisoformat(r["started_at"]),
            status=AttemptStatus(r["status"]),
            submitted_at=_dt(r.get("submitted_at")),
            grading_result_id=r.get("grading_result_id"),
            exam_session_id=r.get("exam_session_id"),
            isolation_key=r.get("isolation_key"),
        )
