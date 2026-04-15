"""SQLite-backed org store — persistent implementation of OrgRepositoryProtocol.

Tables:
  organizations    — Organization (tenant-scoped)
  departments      — Department (linked to organization; no direct tenant_id in model)
  teams            — Team (linked to department; no direct tenant_id in model)
  reparent_audit   — ReparentAuditLog (append-only; no tenant_id in model)

Architecture anchors:
  ARCH_04 — org-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id enforced on organizations; department/team isolation via organization_id FK.

Note: Department and Team do not carry tenant_id in their domain models. Tenant isolation
for departments and teams flows through organization_id (orgs are tenant-scoped). The
get_department / get_team methods mirror InMemoryOrgRepository (no tenant guard on those calls).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import Department, Organization, ReparentAuditLog, Status, Team


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


@runtime_checkable
class OrgRepositoryProtocol(Protocol):
    # Organizations
    def get_organization(self, organization_id: str) -> Optional[Organization]: ...
    def save_organization(self, org: Organization) -> Organization: ...
    def list_organizations(self, tenant_id: str) -> list[Organization]: ...
    def delete_organization(self, organization_id: str) -> None: ...

    # Departments
    def get_department(self, department_id: str) -> Optional[Department]: ...
    def save_department(self, dept: Department) -> Department: ...
    def list_departments_by_org(self, organization_id: str) -> list[Department]: ...
    def list_child_departments(self, parent_department_id: str) -> list[Department]: ...
    def delete_department(self, department_id: str) -> None: ...

    # Teams
    def get_team(self, team_id: str) -> Optional[Team]: ...
    def save_team(self, team: Team) -> Team: ...
    def list_teams_by_department(self, department_id: str) -> list[Team]: ...
    def delete_team(self, team_id: str) -> None: ...

    # Audit
    def append_reparent_audit(self, log: ReparentAuditLog) -> None: ...
    def list_reparent_audit(self) -> list[ReparentAuditLog]: ...


class SQLiteOrgRepository(BaseRepository):
    """Persistent OrgRepositoryProtocol backed by SQLite.

    Drop-in replacement for InMemoryOrgRepository.
    """

    _SERVICE_NAME = "org-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))
        # Provide same attribute interface as InMemoryOrgRepository for service.py
        # compatibility (service.py accesses repo.organizations[id] = org directly).
        # The SQLite store exposes method-based access only; service.py should use methods.
        self.organizations = _OrgProxy(self)
        self.departments = _DeptProxy(self)
        self.teams = _TeamProxy(self)
        self.departments_by_org: dict[str, set[str]] = {}   # not used — SQL queries instead
        self.department_children: dict[str, set[str]] = {}  # not used — SQL queries instead
        self.teams_by_department: dict[str, set[str]] = {}  # not used — SQL queries instead
        self.org_children: dict[str, set[str]] = {}         # not used — SQL queries instead
        self.reparent_audit_logs: list[ReparentAuditLog] = []  # not used — SQL queries instead

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS organizations (
                    organization_id         TEXT PRIMARY KEY NOT NULL,
                    tenant_id               TEXT NOT NULL,
                    name                    TEXT NOT NULL,
                    code                    TEXT NOT NULL,
                    primary_admin_user_id   TEXT,
                    timezone                TEXT NOT NULL DEFAULT 'UTC',
                    locale                  TEXT NOT NULL DEFAULT 'en-US',
                    parent_organization_id  TEXT,
                    metadata                TEXT NOT NULL DEFAULT '{}',
                    status                  TEXT NOT NULL DEFAULT 'active',
                    created_at              TEXT NOT NULL,
                    updated_at              TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_orgs_tenant
                    ON organizations (tenant_id, status);

                CREATE TABLE IF NOT EXISTS departments (
                    department_id           TEXT PRIMARY KEY NOT NULL,
                    organization_id         TEXT NOT NULL,
                    name                    TEXT NOT NULL,
                    code                    TEXT NOT NULL,
                    department_head_user_id TEXT,
                    cost_center             TEXT,
                    parent_department_id    TEXT,
                    metadata                TEXT NOT NULL DEFAULT '{}',
                    status                  TEXT NOT NULL DEFAULT 'active',
                    created_at              TEXT NOT NULL,
                    updated_at              TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_depts_org
                    ON departments (organization_id, status);
                CREATE INDEX IF NOT EXISTS idx_depts_parent
                    ON departments (parent_department_id);

                CREATE TABLE IF NOT EXISTS teams (
                    team_id             TEXT PRIMARY KEY NOT NULL,
                    department_id       TEXT NOT NULL,
                    name                TEXT NOT NULL,
                    code                TEXT NOT NULL,
                    team_lead_user_id   TEXT,
                    capacity            INTEGER,
                    metadata            TEXT NOT NULL DEFAULT '{}',
                    status              TEXT NOT NULL DEFAULT 'active',
                    created_at          TEXT NOT NULL,
                    updated_at          TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_teams_dept
                    ON teams (department_id, status);

                CREATE TABLE IF NOT EXISTS reparent_audit (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_user_id   TEXT NOT NULL,
                    entity_type     TEXT NOT NULL,
                    entity_id       TEXT NOT NULL,
                    old_parent_id   TEXT,
                    new_parent_id   TEXT,
                    changed_at      TEXT NOT NULL
                );
            """)

    # ---------------------------------------------------------------- #
    # Organizations                                                     #
    # ---------------------------------------------------------------- #

    def get_organization(self, organization_id: str) -> Optional[Organization]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM organizations WHERE organization_id = ? LIMIT 1",
                (organization_id,),
            ).fetchone()
        return _row_to_org(dict(row)) if row else None

    def save_organization(self, org: Organization) -> Organization:
        self._require_tenant_id(org.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO organizations
                   (organization_id, tenant_id, name, code, primary_admin_user_id,
                    timezone, locale, parent_organization_id, metadata, status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(organization_id) DO UPDATE SET
                       name = excluded.name,
                       primary_admin_user_id = excluded.primary_admin_user_id,
                       timezone = excluded.timezone,
                       locale = excluded.locale,
                       parent_organization_id = excluded.parent_organization_id,
                       metadata = excluded.metadata,
                       status = excluded.status,
                       updated_at = excluded.updated_at""",
                (
                    org.organization_id, org.tenant_id, org.name, org.code,
                    org.primary_admin_user_id, org.timezone, org.locale,
                    org.parent_organization_id, json.dumps(org.metadata),
                    org.status.value, _iso(org.created_at), _iso(org.updated_at),
                ),
            )
        return org

    def list_organizations(self, tenant_id: str) -> list[Organization]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM organizations WHERE tenant_id = ? ORDER BY created_at ASC",
                (tid,),
            ).fetchall()
        return [_row_to_org(dict(r)) for r in rows]

    def delete_organization(self, organization_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM organizations WHERE organization_id = ?", (organization_id,)
            )

    # ---------------------------------------------------------------- #
    # Departments                                                       #
    # ---------------------------------------------------------------- #

    def get_department(self, department_id: str) -> Optional[Department]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM departments WHERE department_id = ? LIMIT 1",
                (department_id,),
            ).fetchone()
        return _row_to_dept(dict(row)) if row else None

    def save_department(self, dept: Department) -> Department:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO departments
                   (department_id, organization_id, name, code, department_head_user_id,
                    cost_center, parent_department_id, metadata, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(department_id) DO UPDATE SET
                       name = excluded.name,
                       department_head_user_id = excluded.department_head_user_id,
                       cost_center = excluded.cost_center,
                       parent_department_id = excluded.parent_department_id,
                       metadata = excluded.metadata,
                       status = excluded.status,
                       updated_at = excluded.updated_at""",
                (
                    dept.department_id, dept.organization_id, dept.name, dept.code,
                    dept.department_head_user_id, dept.cost_center,
                    dept.parent_department_id, json.dumps(dept.metadata),
                    dept.status.value, _iso(dept.created_at), _iso(dept.updated_at),
                ),
            )
        return dept

    def list_departments_by_org(self, organization_id: str) -> list[Department]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM departments WHERE organization_id = ? ORDER BY created_at ASC",
                (organization_id,),
            ).fetchall()
        return [_row_to_dept(dict(r)) for r in rows]

    def list_child_departments(self, parent_department_id: str) -> list[Department]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM departments WHERE parent_department_id = ? ORDER BY created_at ASC",
                (parent_department_id,),
            ).fetchall()
        return [_row_to_dept(dict(r)) for r in rows]

    def delete_department(self, department_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM departments WHERE department_id = ?", (department_id,)
            )

    # ---------------------------------------------------------------- #
    # Teams                                                             #
    # ---------------------------------------------------------------- #

    def get_team(self, team_id: str) -> Optional[Team]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM teams WHERE team_id = ? LIMIT 1", (team_id,)
            ).fetchone()
        return _row_to_team(dict(row)) if row else None

    def save_team(self, team: Team) -> Team:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO teams
                   (team_id, department_id, name, code, team_lead_user_id, capacity,
                    metadata, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(team_id) DO UPDATE SET
                       name = excluded.name,
                       team_lead_user_id = excluded.team_lead_user_id,
                       capacity = excluded.capacity,
                       metadata = excluded.metadata,
                       status = excluded.status,
                       updated_at = excluded.updated_at""",
                (
                    team.team_id, team.department_id, team.name, team.code,
                    team.team_lead_user_id, team.capacity, json.dumps(team.metadata),
                    team.status.value, _iso(team.created_at), _iso(team.updated_at),
                ),
            )
        return team

    def list_teams_by_department(self, department_id: str) -> list[Team]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM teams WHERE department_id = ? ORDER BY created_at ASC",
                (department_id,),
            ).fetchall()
        return [_row_to_team(dict(r)) for r in rows]

    def delete_team(self, team_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))

    # ---------------------------------------------------------------- #
    # Reparent audit                                                    #
    # ---------------------------------------------------------------- #

    def append_reparent_audit(self, log: ReparentAuditLog) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO reparent_audit
                   (actor_user_id, entity_type, entity_id, old_parent_id, new_parent_id, changed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    log.actor_user_id, log.entity_type, log.entity_id,
                    log.old_parent_id, log.new_parent_id, _iso(log.changed_at),
                ),
            )

    def list_reparent_audit(self) -> list[ReparentAuditLog]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM reparent_audit ORDER BY changed_at ASC"
            ).fetchall()
        return [
            ReparentAuditLog(
                actor_user_id=r["actor_user_id"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                old_parent_id=r["old_parent_id"],
                new_parent_id=r["new_parent_id"],
                changed_at=datetime.fromisoformat(r["changed_at"]),
            )
            for r in rows
        ]


# ---------------------------------------------------------------- #
# Proxy objects — dict-interface compatibility for service.py      #
# (service.py does repo.organizations[id] = org directly)          #
# ---------------------------------------------------------------- #

class _OrgProxy:
    """Thin dict-like proxy that delegates reads/writes to SQLiteOrgRepository."""
    def __init__(self, repo: SQLiteOrgRepository) -> None:
        self._repo = repo

    def __setitem__(self, org_id: str, org: Organization) -> None:
        self._repo.save_organization(org)

    def __getitem__(self, org_id: str) -> Organization:
        result = self._repo.get_organization(org_id)
        if result is None:
            raise KeyError(org_id)
        return result

    def get(self, org_id: str, default=None):
        return self._repo.get_organization(org_id) or default

    def __contains__(self, org_id: str) -> bool:
        return self._repo.get_organization(org_id) is not None

    def __delitem__(self, org_id: str) -> None:
        self._repo.delete_organization(org_id)


class _DeptProxy:
    def __init__(self, repo: SQLiteOrgRepository) -> None:
        self._repo = repo

    def __setitem__(self, dept_id: str, dept: Department) -> None:
        self._repo.save_department(dept)

    def __getitem__(self, dept_id: str) -> Department:
        result = self._repo.get_department(dept_id)
        if result is None:
            raise KeyError(dept_id)
        return result

    def get(self, dept_id: str, default=None):
        return self._repo.get_department(dept_id) or default

    def __contains__(self, dept_id: str) -> bool:
        return self._repo.get_department(dept_id) is not None

    def __delitem__(self, dept_id: str) -> None:
        self._repo.delete_department(dept_id)


class _TeamProxy:
    def __init__(self, repo: SQLiteOrgRepository) -> None:
        self._repo = repo

    def __setitem__(self, team_id: str, team: Team) -> None:
        self._repo.save_team(team)

    def __getitem__(self, team_id: str) -> Team:
        result = self._repo.get_team(team_id)
        if result is None:
            raise KeyError(team_id)
        return result

    def get(self, team_id: str, default=None):
        return self._repo.get_team(team_id) or default

    def __contains__(self, team_id: str) -> bool:
        return self._repo.get_team(team_id) is not None

    def __delitem__(self, team_id: str) -> None:
        self._repo.delete_team(team_id)


# ---------------------------------------------------------------- #
# Deserialisation helpers                                           #
# ---------------------------------------------------------------- #

def _row_to_org(r: dict) -> Organization:
    return Organization(
        organization_id=r["organization_id"],
        tenant_id=r["tenant_id"],
        name=r["name"],
        code=r["code"],
        primary_admin_user_id=r.get("primary_admin_user_id"),
        timezone=r.get("timezone", "UTC"),
        locale=r.get("locale", "en-US"),
        parent_organization_id=r.get("parent_organization_id"),
        metadata=json.loads(r["metadata"]),
        status=Status(r["status"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )


def _row_to_dept(r: dict) -> Department:
    return Department(
        department_id=r["department_id"],
        organization_id=r["organization_id"],
        name=r["name"],
        code=r["code"],
        department_head_user_id=r.get("department_head_user_id"),
        cost_center=r.get("cost_center"),
        parent_department_id=r.get("parent_department_id"),
        metadata=json.loads(r["metadata"]),
        status=Status(r["status"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )


def _row_to_team(r: dict) -> Team:
    return Team(
        team_id=r["team_id"],
        department_id=r["department_id"],
        name=r["name"],
        code=r["code"],
        team_lead_user_id=r.get("team_lead_user_id"),
        capacity=r.get("capacity"),
        metadata=json.loads(r["metadata"]),
        status=Status(r["status"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )
