"""SQLite-backed program store — persistent implementation of ProgramStore Protocol.

Tables:
  programs — Program (tenant-scoped; nested fields as JSON columns)

Architecture anchors:
  ARCH_04 — program-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on programs; tenant-first list/code_exists queries.

Note: ProgramStore.get(program_id) has no tenant_id parameter — matches Protocol as-is.
      list_by_tenant and code_exists enforce tenant isolation.
      Soft-delete via `deleted` boolean column — list_by_tenant excludes deleted records.
      Nested fields serialised as JSON: institution_link, course_mappings, status_history.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    LinkStatus,
    MappingStatus,
    Program,
    ProgramCourseMap,
    ProgramInstitutionLink,
    ProgramStatus,
    ProgramStatusHistory,
    ProgramVisibility,
)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def _isodate(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _date(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


class SQLiteProgramStore(BaseRepository):
    """Persistent ProgramStore backed by SQLite.

    Implements ProgramStore Protocol — drop-in for InMemoryProgramStore.
    """

    _SERVICE_NAME = "program-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS programs (
                    program_id          TEXT PRIMARY KEY NOT NULL,
                    tenant_id           TEXT NOT NULL,
                    institution_id      TEXT NOT NULL,
                    code                TEXT NOT NULL,
                    title               TEXT NOT NULL,
                    description         TEXT,
                    status              TEXT NOT NULL DEFAULT 'draft',
                    version             INTEGER NOT NULL DEFAULT 1,
                    visibility          TEXT NOT NULL DEFAULT 'private',
                    start_date          TEXT,
                    end_date            TEXT,
                    metadata            TEXT NOT NULL DEFAULT '{}',
                    created_by          TEXT NOT NULL,
                    updated_by          TEXT NOT NULL,
                    created_at          TEXT NOT NULL,
                    updated_at          TEXT NOT NULL,
                    mapping_version     INTEGER NOT NULL DEFAULT 0,
                    deleted             INTEGER NOT NULL DEFAULT 0,
                    institution_link    TEXT,
                    course_mappings     TEXT NOT NULL DEFAULT '[]',
                    status_history      TEXT NOT NULL DEFAULT '[]'
                );
                CREATE INDEX IF NOT EXISTS idx_programs_tenant
                    ON programs (tenant_id, deleted, status);
                CREATE INDEX IF NOT EXISTS idx_programs_code
                    ON programs (tenant_id, code, deleted);
            """)

    # ---------------------------------------------------------------- #
    # ProgramStore Protocol                                             #
    # ---------------------------------------------------------------- #

    def create(self, program: Program) -> Program:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO programs
                   (program_id, tenant_id, institution_id, code, title, description,
                    status, version, visibility, start_date, end_date, metadata,
                    created_by, updated_by, created_at, updated_at,
                    mapping_version, deleted, institution_link, course_mappings, status_history)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                _program_to_row(program),
            )
        return program

    def update(self, program: Program) -> Program:
        with self._connect() as conn:
            conn.execute(
                """UPDATE programs SET
                   tenant_id = ?, institution_id = ?, code = ?, title = ?,
                   description = ?, status = ?, version = ?, visibility = ?,
                   start_date = ?, end_date = ?, metadata = ?,
                   created_by = ?, updated_by = ?, created_at = ?, updated_at = ?,
                   mapping_version = ?, deleted = ?,
                   institution_link = ?, course_mappings = ?, status_history = ?
                   WHERE program_id = ?""",
                _program_to_row(program)[1:] + (_program_to_row(program)[0],),
            )
        return program

    def get(self, program_id: str) -> Program | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM programs WHERE program_id = ? LIMIT 1", (program_id,)
            ).fetchone()
        return _row_to_program(dict(row)) if row else None

    def list_by_tenant(self, tenant_id: str) -> list[Program]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM programs
                   WHERE tenant_id = ? AND deleted = 0
                   ORDER BY created_at ASC""",
                (tid,),
            ).fetchall()
        return [_row_to_program(dict(r)) for r in rows]

    def code_exists(self, tenant_id: str, code: str) -> bool:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = conn.execute(
                """SELECT 1 FROM programs
                   WHERE tenant_id = ? AND code = ? AND deleted = 0
                   LIMIT 1""",
                (tid, code),
            ).fetchone()
        return row is not None


# ---------------------------------------------------------------- #
# Serialisation / deserialisation helpers                          #
# ---------------------------------------------------------------- #

def _dump_institution_link(link: ProgramInstitutionLink | None) -> str | None:
    if link is None:
        return None
    return json.dumps({
        "program_id": link.program_id,
        "institution_id": link.institution_id,
        "link_status": link.link_status.value,
        "linked_at": _iso(link.linked_at),
        "unlinked_at": _iso(link.unlinked_at),
        "link_metadata": link.link_metadata,
    })


def _load_institution_link(s: str | None) -> ProgramInstitutionLink | None:
    if not s:
        return None
    d = json.loads(s)
    return ProgramInstitutionLink(
        program_id=d["program_id"],
        institution_id=d["institution_id"],
        link_status=LinkStatus(d["link_status"]),
        linked_at=_dt(d.get("linked_at")),
        unlinked_at=_dt(d.get("unlinked_at")),
        link_metadata=d.get("link_metadata", {}),
    )


def _dump_course_mappings(mappings: list[ProgramCourseMap]) -> str:
    return json.dumps([
        {
            "program_id": m.program_id,
            "course_id": m.course_id,
            "sequence_order": m.sequence_order,
            "is_required": m.is_required,
            "minimum_completion_pct": m.minimum_completion_pct,
            "availability_rule": m.availability_rule,
            "mapping_status": m.mapping_status.value,
            "mapped_at": _iso(m.mapped_at),
            "unmapped_at": _iso(m.unmapped_at),
        }
        for m in mappings
    ])


def _load_course_mappings(s: str) -> list[ProgramCourseMap]:
    return [
        ProgramCourseMap(
            program_id=d["program_id"],
            course_id=d["course_id"],
            sequence_order=d["sequence_order"],
            is_required=d["is_required"],
            minimum_completion_pct=d.get("minimum_completion_pct"),
            availability_rule=d.get("availability_rule"),
            mapping_status=MappingStatus(d["mapping_status"]),
            mapped_at=_dt(d.get("mapped_at")),
            unmapped_at=_dt(d.get("unmapped_at")),
        )
        for d in json.loads(s)
    ]


def _dump_status_history(history: list[ProgramStatusHistory]) -> str:
    return json.dumps([
        {
            "program_id": h.program_id,
            "from_status": h.from_status.value,
            "to_status": h.to_status.value,
            "changed_by": h.changed_by,
            "change_reason": h.change_reason,
            "changed_at": _iso(h.changed_at),
        }
        for h in history
    ])


def _load_status_history(s: str) -> list[ProgramStatusHistory]:
    return [
        ProgramStatusHistory(
            program_id=d["program_id"],
            from_status=ProgramStatus(d["from_status"]),
            to_status=ProgramStatus(d["to_status"]),
            changed_by=d["changed_by"],
            change_reason=d["change_reason"],
            changed_at=datetime.fromisoformat(d["changed_at"]),
        )
        for d in json.loads(s)
    ]


def _program_to_row(p: Program) -> tuple:
    return (
        p.program_id, p.tenant_id, p.institution_id, p.code, p.title, p.description,
        p.status.value, p.version, p.visibility.value,
        _isodate(p.start_date), _isodate(p.end_date),
        json.dumps(p.metadata),
        p.created_by, p.updated_by, _iso(p.created_at), _iso(p.updated_at),
        p.mapping_version, int(p.deleted),
        _dump_institution_link(p.institution_link),
        _dump_course_mappings(p.course_mappings),
        _dump_status_history(p.status_history),
    )


def _row_to_program(r: dict) -> Program:
    return Program(
        program_id=r["program_id"],
        tenant_id=r["tenant_id"],
        institution_id=r["institution_id"],
        code=r["code"],
        title=r["title"],
        description=r.get("description"),
        status=ProgramStatus(r["status"]),
        version=r["version"],
        visibility=ProgramVisibility(r["visibility"]),
        start_date=_date(r.get("start_date")),
        end_date=_date(r.get("end_date")),
        metadata=json.loads(r["metadata"]),
        created_by=r["created_by"],
        updated_by=r["updated_by"],
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
        mapping_version=r["mapping_version"],
        deleted=bool(r["deleted"]),
        institution_link=_load_institution_link(r.get("institution_link")),
        course_mappings=_load_course_mappings(r.get("course_mappings", "[]")),
        status_history=_load_status_history(r.get("status_history", "[]")),
    )
