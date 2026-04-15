"""SQLite-backed cohort store — persistent implementation of CohortStore Protocol.

Tables:
  cohorts     — CohortRecord (tenant-scoped; schedule as JSON)
  memberships — MembershipRecord (tenant-scoped)

Architecture anchors:
  ARCH_04 — cohort-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import CohortRecord, MembershipRecord
from .schemas import CohortKind, CohortSchedule, CohortStatus


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SQLiteCohortStore(BaseRepository):
    """Persistent CohortStore backed by SQLite.

    Implements CohortStore Protocol — drop-in for InMemoryCohortStore.
    """

    _SERVICE_NAME = "cohort-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cohorts (
                    cohort_id   TEXT NOT NULL,
                    tenant_id   TEXT NOT NULL,
                    name        TEXT NOT NULL,
                    code        TEXT NOT NULL,
                    kind        TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'draft',
                    schedule    TEXT NOT NULL DEFAULT '{}',
                    program_id  TEXT,
                    metadata    TEXT NOT NULL DEFAULT '{}',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    created_by  TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, cohort_id)
                );
                CREATE INDEX IF NOT EXISTS idx_cohorts_tenant
                    ON cohorts (tenant_id, status);

                CREATE TABLE IF NOT EXISTS memberships (
                    membership_id   TEXT NOT NULL,
                    cohort_id       TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    user_id         TEXT NOT NULL,
                    role            TEXT NOT NULL,
                    joined_at       TEXT NOT NULL,
                    added_by        TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, membership_id)
                );
                CREATE INDEX IF NOT EXISTS idx_memberships_cohort
                    ON memberships (tenant_id, cohort_id);
            """)

    # ---------------------------------------------------------------- #
    # CohortStore Protocol — cohorts                                   #
    # ---------------------------------------------------------------- #

    def save_cohort(self, cohort: CohortRecord) -> CohortRecord:
        tid = self._require_tenant_id(cohort.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO cohorts
                   (cohort_id, tenant_id, name, code, kind, status, schedule,
                    program_id, metadata, created_at, updated_at, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, cohort_id) DO UPDATE SET
                       name = excluded.name,
                       kind = excluded.kind,
                       status = excluded.status,
                       schedule = excluded.schedule,
                       program_id = excluded.program_id,
                       metadata = excluded.metadata,
                       updated_at = excluded.updated_at""",
                (
                    cohort.cohort_id, tid, cohort.name, cohort.code,
                    cohort.kind.value, cohort.status.value,
                    cohort.schedule.model_dump_json(),
                    cohort.program_id, json.dumps(cohort.metadata),
                    _iso(cohort.created_at), _iso(cohort.updated_at), cohort.created_by,
                ),
            )
        return cohort

    def get_cohort(self, tenant_id: str, cohort_id: str) -> CohortRecord | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "cohorts", tid, "AND cohort_id = ?", (cohort_id,)
            )
        return _row_to_cohort(dict(row)) if row else None

    def list_cohorts(self, tenant_id: str) -> list[CohortRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "cohorts", tid, order_by="created_at ASC")
        return [_row_to_cohort(dict(r)) for r in rows]

    def delete_cohort(self, tenant_id: str, cohort_id: str) -> None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM cohorts WHERE tenant_id = ? AND cohort_id = ?",
                (tid, cohort_id),
            )

    # ---------------------------------------------------------------- #
    # CohortStore Protocol — memberships                               #
    # ---------------------------------------------------------------- #

    def save_membership(self, membership: MembershipRecord) -> MembershipRecord:
        tid = self._require_tenant_id(membership.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO memberships
                   (membership_id, cohort_id, tenant_id, user_id, role, joined_at, added_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, membership_id) DO UPDATE SET
                       role = excluded.role""",
                (
                    membership.membership_id, membership.cohort_id, tid,
                    membership.user_id, membership.role,
                    _iso(membership.joined_at), membership.added_by,
                ),
            )
        return membership

    def remove_membership(
        self, tenant_id: str, cohort_id: str, membership_id: str
    ) -> None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                """DELETE FROM memberships
                   WHERE tenant_id = ? AND cohort_id = ? AND membership_id = ?""",
                (tid, cohort_id, membership_id),
            )

    def list_memberships(self, tenant_id: str, cohort_id: str) -> list[MembershipRecord]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "memberships", tid,
                "AND cohort_id = ?", (cohort_id,),
                order_by="joined_at ASC",
            )
        return [_row_to_membership(dict(r)) for r in rows]


# ---------------------------------------------------------------- #
# Deserialisation helpers                                           #
# ---------------------------------------------------------------- #

def _row_to_cohort(r: dict) -> CohortRecord:
    return CohortRecord(
        cohort_id=r["cohort_id"],
        tenant_id=r["tenant_id"],
        name=r["name"],
        code=r["code"],
        kind=CohortKind(r["kind"]),
        status=CohortStatus(r["status"]),
        schedule=CohortSchedule.model_validate_json(r["schedule"]),
        program_id=r.get("program_id"),
        metadata=json.loads(r["metadata"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
        created_by=r["created_by"],
    )


def _row_to_membership(r: dict) -> MembershipRecord:
    return MembershipRecord(
        membership_id=r["membership_id"],
        cohort_id=r["cohort_id"],
        tenant_id=r["tenant_id"],
        user_id=r["user_id"],
        role=r["role"],
        joined_at=datetime.fromisoformat(r["joined_at"]),
        added_by=r["added_by"],
    )
