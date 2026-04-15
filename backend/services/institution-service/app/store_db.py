"""SQLite-backed institution store — persistent InstitutionRepository backed by SQLite.

Tables:
  institutions            — Institution (tenant-scoped)
  institution_types       — InstitutionType (global catalog — no tenant_id)
  institution_hierarchy_edges — InstitutionHierarchyEdge (cross-institution; no tenant_id)
  institution_tenant_links — InstitutionTenantLink (tenant-scoped)

Architecture anchors:
  ARCH_04 — institution-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on tenant-scoped tables. Types and hierarchy edges are
            global platform infrastructure (no tenant_id — same pattern as rbac_permissions).

Note: InstitutionRepository wraps InMemoryInstitutionStore. SQLiteInstitutionRepository
      replaces the full Repository+Store stack as a single class — it implements all methods
      from InstitutionRepository directly against SQLite.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    Institution,
    InstitutionHierarchyEdge,
    InstitutionStatus,
    InstitutionTenantLink,
    InstitutionType,
    LinkScope,
    RelationshipType,
)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


@runtime_checkable
class InstitutionRepositoryProtocol(Protocol):
    def save_institution(self, institution: Institution) -> Institution: ...
    def get_institution(self, institution_id: str) -> Optional[Institution]: ...
    def list_tenant_institutions(self, tenant_id: str) -> list[Institution]: ...
    def save_type(self, institution_type: InstitutionType) -> InstitutionType: ...
    def get_type(self, type_code: str) -> Optional[InstitutionType]: ...
    def list_types(self) -> list[InstitutionType]: ...
    def save_hierarchy_edge(self, edge: InstitutionHierarchyEdge) -> InstitutionHierarchyEdge: ...
    def list_edges_for_child(self, child_id: str) -> list[InstitutionHierarchyEdge]: ...
    def list_edges_for_parent(self, parent_id: str) -> list[InstitutionHierarchyEdge]: ...
    def deactivate_edge(self, child_id: str, parent_id: str) -> Optional[InstitutionHierarchyEdge]: ...
    def save_tenant_link(self, link: InstitutionTenantLink) -> InstitutionTenantLink: ...
    def list_tenant_links(self, institution_id: str) -> list[InstitutionTenantLink]: ...
    def list_links_for_tenant(self, tenant_id: str) -> list[InstitutionTenantLink]: ...
    def deactivate_link(self, link_id: str) -> Optional[InstitutionTenantLink]: ...


class SQLiteInstitutionRepository(BaseRepository):
    """Persistent InstitutionRepositoryProtocol backed by SQLite.

    Drop-in replacement for InstitutionRepository(InMemoryInstitutionStore()).
    Seeds SYSTEM_INSTITUTION_TYPES on first run.
    """

    _SERVICE_NAME = "institution-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))
        self._seed_system_types()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS institutions (
                    institution_id          TEXT PRIMARY KEY NOT NULL,
                    institution_type        TEXT NOT NULL,
                    legal_name              TEXT NOT NULL,
                    display_name            TEXT NOT NULL,
                    tenant_id               TEXT NOT NULL,
                    status                  TEXT NOT NULL DEFAULT 'draft',
                    registration_country    TEXT,
                    default_locale          TEXT NOT NULL DEFAULT 'en-US',
                    timezone                TEXT NOT NULL DEFAULT 'UTC',
                    metadata                TEXT NOT NULL DEFAULT '{}',
                    created_at              TEXT NOT NULL,
                    updated_at              TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_institutions_tenant
                    ON institutions (tenant_id, status);

                CREATE TABLE IF NOT EXISTS institution_types (
                    type_code           TEXT PRIMARY KEY NOT NULL,
                    type_name           TEXT NOT NULL,
                    governance_profile  TEXT NOT NULL DEFAULT '{}',
                    is_system_type      INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS institution_hierarchy_edges (
                    edge_id                     TEXT PRIMARY KEY NOT NULL,
                    parent_institution_id       TEXT NOT NULL,
                    child_institution_id        TEXT NOT NULL,
                    relationship_type           TEXT NOT NULL,
                    status                      TEXT NOT NULL DEFAULT 'active',
                    effective_from              TEXT NOT NULL,
                    effective_to                TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_edges_child
                    ON institution_hierarchy_edges (child_institution_id, status);
                CREATE INDEX IF NOT EXISTS idx_edges_parent
                    ON institution_hierarchy_edges (parent_institution_id, status);

                CREATE TABLE IF NOT EXISTS institution_tenant_links (
                    link_id         TEXT PRIMARY KEY NOT NULL,
                    institution_id  TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    link_scope      TEXT NOT NULL,
                    status          TEXT NOT NULL DEFAULT 'active',
                    linked_at       TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_links_institution
                    ON institution_tenant_links (institution_id);
                CREATE INDEX IF NOT EXISTS idx_links_tenant
                    ON institution_tenant_links (tenant_id, status);
            """)

    def _seed_system_types(self) -> None:
        from .models import SYSTEM_INSTITUTION_TYPES
        with self._connect() as conn:
            for code in SYSTEM_INSTITUTION_TYPES:
                conn.execute(
                    """INSERT OR IGNORE INTO institution_types
                       (type_code, type_name, governance_profile, is_system_type)
                       VALUES (?, ?, ?, 1)""",
                    (code, code.replace("_", " ").title(), "{}", ),
                )

    # ---------------------------------------------------------------- #
    # Institutions                                                      #
    # ---------------------------------------------------------------- #

    def save_institution(self, institution: Institution) -> Institution:
        self._require_tenant_id(institution.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO institutions
                   (institution_id, institution_type, legal_name, display_name, tenant_id,
                    status, registration_country, default_locale, timezone, metadata,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(institution_id) DO UPDATE SET
                       institution_type = excluded.institution_type,
                       legal_name = excluded.legal_name,
                       display_name = excluded.display_name,
                       status = excluded.status,
                       registration_country = excluded.registration_country,
                       default_locale = excluded.default_locale,
                       timezone = excluded.timezone,
                       metadata = excluded.metadata,
                       updated_at = excluded.updated_at""",
                (
                    institution.institution_id, institution.institution_type,
                    institution.legal_name, institution.display_name, institution.tenant_id,
                    institution.status.value, institution.registration_country,
                    institution.default_locale, institution.timezone,
                    json.dumps(institution.metadata),
                    _iso(institution.created_at), _iso(institution.updated_at),
                ),
            )
        return institution

    def get_institution(self, institution_id: str) -> Optional[Institution]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM institutions WHERE institution_id = ? LIMIT 1",
                (institution_id,),
            ).fetchone()
        return _row_to_institution(dict(row)) if row else None

    def list_tenant_institutions(self, tenant_id: str) -> list[Institution]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM institutions WHERE tenant_id = ? ORDER BY created_at ASC",
                (tid,),
            ).fetchall()
        return [_row_to_institution(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # Institution types (global catalog)                               #
    # ---------------------------------------------------------------- #

    def save_type(self, institution_type: InstitutionType) -> InstitutionType:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO institution_types
                   (type_code, type_name, governance_profile, is_system_type)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(type_code) DO UPDATE SET
                       type_name = excluded.type_name,
                       governance_profile = excluded.governance_profile""",
                (
                    institution_type.type_code, institution_type.type_name,
                    json.dumps(institution_type.governance_profile),
                    int(institution_type.is_system_type),
                ),
            )
        return institution_type

    def get_type(self, type_code: str) -> Optional[InstitutionType]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM institution_types WHERE type_code = ? LIMIT 1", (type_code,)
            ).fetchone()
        return _row_to_type(dict(row)) if row else None

    def list_types(self) -> list[InstitutionType]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM institution_types ORDER BY type_code ASC"
            ).fetchall()
        return [_row_to_type(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # Hierarchy edges                                                   #
    # ---------------------------------------------------------------- #

    def save_hierarchy_edge(self, edge: InstitutionHierarchyEdge) -> InstitutionHierarchyEdge:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO institution_hierarchy_edges
                   (edge_id, parent_institution_id, child_institution_id,
                    relationship_type, status, effective_from, effective_to)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(edge_id) DO UPDATE SET
                       status = excluded.status,
                       effective_to = excluded.effective_to""",
                (
                    edge.edge_id, edge.parent_institution_id, edge.child_institution_id,
                    edge.relationship_type.value, edge.status,
                    _iso(edge.effective_from), _iso(edge.effective_to),
                ),
            )
        return edge

    def list_edges_for_child(self, child_id: str) -> list[InstitutionHierarchyEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM institution_hierarchy_edges
                   WHERE child_institution_id = ? AND status = 'active'""",
                (child_id,),
            ).fetchall()
        return [_row_to_edge(dict(r)) for r in rows]

    def list_edges_for_parent(self, parent_id: str) -> list[InstitutionHierarchyEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM institution_hierarchy_edges
                   WHERE parent_institution_id = ? AND status = 'active'""",
                (parent_id,),
            ).fetchall()
        return [_row_to_edge(dict(r)) for r in rows]

    def deactivate_edge(
        self, child_id: str, parent_id: str
    ) -> Optional[InstitutionHierarchyEdge]:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM institution_hierarchy_edges
                   WHERE child_institution_id = ? AND parent_institution_id = ?
                   AND status = 'active' LIMIT 1""",
                (child_id, parent_id),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """UPDATE institution_hierarchy_edges SET status = 'inactive'
                   WHERE edge_id = ?""",
                (row["edge_id"],),
            )
        edge = _row_to_edge(dict(row))
        edge.status = "inactive"
        return edge

    # ---------------------------------------------------------------- #
    # Tenant links                                                      #
    # ---------------------------------------------------------------- #

    def save_tenant_link(self, link: InstitutionTenantLink) -> InstitutionTenantLink:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO institution_tenant_links
                   (link_id, institution_id, tenant_id, link_scope, status, linked_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(link_id) DO UPDATE SET
                       status = excluded.status""",
                (
                    link.link_id, link.institution_id, link.tenant_id,
                    link.link_scope.value, link.status, _iso(link.linked_at),
                ),
            )
        return link

    def list_tenant_links(self, institution_id: str) -> list[InstitutionTenantLink]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM institution_tenant_links WHERE institution_id = ?",
                (institution_id,),
            ).fetchall()
        return [_row_to_link(dict(r)) for r in rows]

    def list_links_for_tenant(self, tenant_id: str) -> list[InstitutionTenantLink]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM institution_tenant_links
                   WHERE tenant_id = ? AND status = 'active'""",
                (tid,),
            ).fetchall()
        return [_row_to_link(dict(r)) for r in rows]

    def deactivate_link(self, link_id: str) -> Optional[InstitutionTenantLink]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM institution_tenant_links WHERE link_id = ? LIMIT 1",
                (link_id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE institution_tenant_links SET status = 'inactive' WHERE link_id = ?",
                (link_id,),
            )
        link = _row_to_link(dict(row))
        link.status = "inactive"
        return link


# ---------------------------------------------------------------- #
# Deserialisation helpers                                           #
# ---------------------------------------------------------------- #

def _row_to_institution(r: dict) -> Institution:
    return Institution(
        institution_id=r["institution_id"],
        institution_type=r["institution_type"],
        legal_name=r["legal_name"],
        display_name=r["display_name"],
        tenant_id=r["tenant_id"],
        status=InstitutionStatus(r["status"]),
        registration_country=r.get("registration_country"),
        default_locale=r.get("default_locale", "en-US"),
        timezone=r.get("timezone", "UTC"),
        metadata=json.loads(r["metadata"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )


def _row_to_type(r: dict) -> InstitutionType:
    return InstitutionType(
        type_code=r["type_code"],
        type_name=r["type_name"],
        governance_profile=json.loads(r["governance_profile"]),
        is_system_type=bool(r["is_system_type"]),
    )


def _row_to_edge(r: dict) -> InstitutionHierarchyEdge:
    return InstitutionHierarchyEdge(
        edge_id=r["edge_id"],
        parent_institution_id=r["parent_institution_id"],
        child_institution_id=r["child_institution_id"],
        relationship_type=RelationshipType(r["relationship_type"]),
        status=r["status"],
        effective_from=datetime.fromisoformat(r["effective_from"]),
        effective_to=_dt(r.get("effective_to")),
    )


def _row_to_link(r: dict) -> InstitutionTenantLink:
    return InstitutionTenantLink(
        link_id=r["link_id"],
        institution_id=r["institution_id"],
        tenant_id=r["tenant_id"],
        link_scope=LinkScope(r["link_scope"]),
        status=r["status"],
        linked_at=datetime.fromisoformat(r["linked_at"]),
    )
