"""SQLite-backed RBAC store — persistent replacement for InMemoryRBACStore.

Implements RBACStoreProtocol; service.py can inject either implementation.

Tables (per SPEC_03 §2 — 6 owned entities):
  rbac_roles              — RoleDefinition, tenant-scoped
  rbac_permissions        — PermissionDefinition, global catalog (no tenant_id)
  rbac_role_permissions   — role → permission_key bindings, tenant-scoped
  rbac_assignments        — SubjectRoleAssignment, tenant-scoped
  rbac_policy_rules       — PolicyRule, tenant-scoped
  rbac_decision_logs      — AuthorizationDecisionLog, append-only, tenant-scoped

Architecture anchors:
  ARCH_04 — rbac-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tenant-owned tables;
             rbac_permissions is a global platform catalog (exempted from tenant_id).
  SPEC_03 §3 — every mutable RBAC object partitioned by tenant_id;
               cross-tenant role assignment forbidden.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    AuthorizationDecisionLog,
    PermissionDefinition,
    PolicyRule,
    RoleDefinition,
    SubjectRoleAssignment,
)


# ──────────────────────────────────────────────────────────────────── #
# Protocol                                                             #
# ──────────────────────────────────────────────────────────────────── #

@runtime_checkable
class RBACStoreProtocol(Protocol):
    """Structural contract shared by InMemoryRBACStore and SQLiteRBACStore."""

    def create_role(self, role: RoleDefinition) -> RoleDefinition: ...
    def list_roles(self, tenant_id: str) -> list[RoleDefinition]: ...
    def get_role(self, tenant_id: str, role_id: str) -> RoleDefinition | None: ...
    def update_role(self, role: RoleDefinition) -> RoleDefinition: ...

    def list_permissions(self) -> list[PermissionDefinition]: ...

    def put_role_permissions(self, tenant_id: str, role_id: str, permission_keys: list[str]) -> None: ...
    def get_role_permissions(self, tenant_id: str, role_id: str) -> list[str]: ...

    def create_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment: ...
    def list_assignments(self, tenant_id: str) -> list[SubjectRoleAssignment]: ...
    def get_assignment(self, tenant_id: str, assignment_id: str) -> SubjectRoleAssignment | None: ...
    def update_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment: ...

    def create_policy_rule(self, rule: PolicyRule) -> PolicyRule: ...
    def list_policy_rules(self, tenant_id: str) -> list[PolicyRule]: ...
    def get_policy_rule(self, tenant_id: str, rule_id: str) -> PolicyRule | None: ...
    def update_policy_rule(self, rule: PolicyRule) -> PolicyRule: ...

    def log_decision(self, log: AuthorizationDecisionLog) -> None: ...
    def list_decision_logs(self, tenant_id: str) -> list[AuthorizationDecisionLog]: ...


# ──────────────────────────────────────────────────────────────────── #
# Serialisation helpers                                                #
# ──────────────────────────────────────────────────────────────────── #

def _dump(model) -> str:
    """Serialise a Pydantic model to a JSON string, datetimes as ISO strings."""
    return json.dumps(model.model_dump(mode="json"))


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────── #
# SQLite store                                                         #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteRBACStore(BaseRepository):
    """Persistent, tenant-isolated RBAC store backed by SQLite.

    Usage::

        store = SQLiteRBACStore()          # ./data/rbac-service.db
        store = SQLiteRBACStore(db_path)   # explicit path (tests)
    """

    _SERVICE_NAME = "rbac-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))
        self._permissions = self._load_or_seed_permissions()

    # ---------------------------------------------------------------- #
    # Schema                                                             #
    # ---------------------------------------------------------------- #

    def _init_schema(self) -> None:
        statements = [
            # SPEC_03 §2.1 — RoleDefinition (tenant-scoped)
            """CREATE TABLE IF NOT EXISTS rbac_roles (
                role_id      TEXT PRIMARY KEY,
                tenant_id    TEXT NOT NULL,
                role_key     TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'active',
                data         TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                UNIQUE (tenant_id, role_key)
            )""",
            # SPEC_03 §2.2 — PermissionDefinition (global platform catalog, no tenant_id)
            """CREATE TABLE IF NOT EXISTS rbac_permissions (
                permission_id  TEXT PRIMARY KEY,
                permission_key TEXT UNIQUE NOT NULL,
                data           TEXT NOT NULL
            )""",
            # SPEC_03 §2.3 — RolePermissionBinding (tenant-scoped through role)
            # Stores list of permission_keys per (tenant_id, role_id) —
            # matches InMemoryRBACStore's put_role_permissions / get_role_permissions interface.
            """CREATE TABLE IF NOT EXISTS rbac_role_permissions (
                tenant_id      TEXT NOT NULL,
                role_id        TEXT NOT NULL,
                permission_key TEXT NOT NULL,
                PRIMARY KEY (tenant_id, role_id, permission_key)
            )""",
            # SPEC_03 §2.4 — SubjectRoleAssignment (tenant-scoped)
            """CREATE TABLE IF NOT EXISTS rbac_assignments (
                assignment_id TEXT PRIMARY KEY,
                tenant_id     TEXT NOT NULL,
                subject_id    TEXT NOT NULL,
                role_id       TEXT NOT NULL,
                revoked_at    TEXT,
                data          TEXT NOT NULL
            )""",
            # SPEC_03 §2.5 — PolicyRule (tenant-scoped)
            """CREATE TABLE IF NOT EXISTS rbac_policy_rules (
                policy_rule_id TEXT PRIMARY KEY,
                tenant_id      TEXT NOT NULL,
                rule_type      TEXT NOT NULL,
                priority       INTEGER NOT NULL DEFAULT 100,
                enabled        INTEGER NOT NULL DEFAULT 1,
                data           TEXT NOT NULL
            )""",
            # SPEC_03 §2.6 — AuthorizationDecisionLog (append-only, tenant-scoped)
            """CREATE TABLE IF NOT EXISTS rbac_decision_logs (
                decision_id TEXT PRIMARY KEY,
                tenant_id   TEXT NOT NULL,
                decision    TEXT NOT NULL,
                evaluated_at TEXT NOT NULL,
                data         TEXT NOT NULL
            )""",
        ]
        with self._connect() as conn:
            for stmt in statements:
                conn.execute(stmt)

    # ---------------------------------------------------------------- #
    # Permission catalog — global, seeded once                          #
    # ---------------------------------------------------------------- #

    def _load_or_seed_permissions(self) -> dict[str, PermissionDefinition]:
        """Return in-memory permission catalog, seeding DB defaults on first run."""
        with self._connect() as conn:
            rows = conn.execute("SELECT permission_key, data FROM rbac_permissions").fetchall()

        if rows:
            return {
                r["permission_key"]: PermissionDefinition.model_validate(json.loads(r["data"]))
                for r in rows
            }

        # Seed the default catalog (mirrors InMemoryRBACStore._seed_permission_catalog)
        defaults = [
            PermissionDefinition(permission_key="audit.view_tenant",      resource_type="audit",  action="view",   risk_tier="moderate"),
            PermissionDefinition(permission_key="tenant.settings.manage",  resource_type="tenant", action="manage", risk_tier="high"),
            PermissionDefinition(permission_key="course.publish",          resource_type="course", action="publish", risk_tier="high"),
            PermissionDefinition(permission_key="course.view",             resource_type="course", action="view",   risk_tier="low"),
        ]
        with self._connect() as conn:
            for p in defaults:
                conn.execute(
                    "INSERT OR IGNORE INTO rbac_permissions (permission_id, permission_key, data) VALUES (?, ?, ?)",
                    (p.permission_id, p.permission_key, _dump(p)),
                )
        return {p.permission_key: p for p in defaults}

    def list_permissions(self) -> list[PermissionDefinition]:
        """Return the global permission catalog (not tenant-scoped per SPEC_03 §2.2)."""
        return list(self._permissions.values())

    def upsert_permission(self, permission: PermissionDefinition) -> None:
        """Add or replace a permission in the global catalog."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO rbac_permissions (permission_id, permission_key, data)
                   VALUES (?, ?, ?)
                   ON CONFLICT(permission_id) DO UPDATE SET
                     permission_key = excluded.permission_key,
                     data = excluded.data""",
                (permission.permission_id, permission.permission_key, _dump(permission)),
            )
        self._permissions[permission.permission_key] = permission

    # ---------------------------------------------------------------- #
    # Role management                                                    #
    # ---------------------------------------------------------------- #

    def create_role(self, role: RoleDefinition) -> RoleDefinition:
        tid = self._require_tenant_id(role.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO rbac_roles
                   (role_id, tenant_id, role_key, status, data, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    role.role_id, tid, role.role_key,
                    role.status.value if hasattr(role.status, "value") else role.status,
                    _dump(role),
                    role.created_at.isoformat(), role.updated_at.isoformat(),
                ),
            )
        return role

    def list_roles(self, tenant_id: str) -> list[RoleDefinition]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "rbac_roles", tid)
        return [RoleDefinition.model_validate(json.loads(r["data"])) for r in rows]

    def get_role(self, tenant_id: str, role_id: str) -> RoleDefinition | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(conn, "rbac_roles", tid, "AND role_id = ?", (role_id,))
        if row is None:
            return None
        return RoleDefinition.model_validate(json.loads(row["data"]))

    def update_role(self, role: RoleDefinition) -> RoleDefinition:
        tid = self._require_tenant_id(role.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE rbac_roles
                   SET role_key = ?, status = ?, data = ?, updated_at = ?
                   WHERE tenant_id = ? AND role_id = ?""",
                (
                    role.role_key,
                    role.status.value if hasattr(role.status, "value") else role.status,
                    _dump(role),
                    _ts(),
                    tid, role.role_id,
                ),
            )
        return role

    # ---------------------------------------------------------------- #
    # Role → permission bindings                                        #
    # ---------------------------------------------------------------- #

    def put_role_permissions(
        self, tenant_id: str, role_id: str, permission_keys: list[str]
    ) -> None:
        """Replace all permission bindings for a role atomically (SPEC_03 §4 PUT semantics)."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM rbac_role_permissions WHERE tenant_id = ? AND role_id = ?",
                (tid, role_id),
            )
            for key in permission_keys:
                conn.execute(
                    "INSERT OR IGNORE INTO rbac_role_permissions (tenant_id, role_id, permission_key) VALUES (?, ?, ?)",
                    (tid, role_id, key),
                )

    def get_role_permissions(self, tenant_id: str, role_id: str) -> list[str]:
        """Return list of permission_key strings for this role in this tenant."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT permission_key FROM rbac_role_permissions WHERE tenant_id = ? AND role_id = ?",
                (tid, role_id),
            ).fetchall()
        return [r["permission_key"] for r in rows]

    # ---------------------------------------------------------------- #
    # Subject role assignments                                           #
    # ---------------------------------------------------------------- #

    def create_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment:
        tid = self._require_tenant_id(assignment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO rbac_assignments
                   (assignment_id, tenant_id, subject_id, role_id, revoked_at, data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    assignment.assignment_id, tid,
                    assignment.subject_id, assignment.role_id,
                    assignment.revoked_at.isoformat() if assignment.revoked_at else None,
                    _dump(assignment),
                ),
            )
        return assignment

    def list_assignments(self, tenant_id: str) -> list[SubjectRoleAssignment]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "rbac_assignments", tid)
        return [SubjectRoleAssignment.model_validate(json.loads(r["data"])) for r in rows]

    def get_assignment(self, tenant_id: str, assignment_id: str) -> SubjectRoleAssignment | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "rbac_assignments", tid, "AND assignment_id = ?", (assignment_id,)
            )
        if row is None:
            return None
        return SubjectRoleAssignment.model_validate(json.loads(row["data"]))

    def update_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment:
        tid = self._require_tenant_id(assignment.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE rbac_assignments
                   SET revoked_at = ?, data = ?
                   WHERE tenant_id = ? AND assignment_id = ?""",
                (
                    assignment.revoked_at.isoformat() if assignment.revoked_at else None,
                    _dump(assignment),
                    tid, assignment.assignment_id,
                ),
            )
        return assignment

    # ---------------------------------------------------------------- #
    # Policy rules                                                       #
    # ---------------------------------------------------------------- #

    def create_policy_rule(self, rule: PolicyRule) -> PolicyRule:
        tid = self._require_tenant_id(rule.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO rbac_policy_rules
                   (policy_rule_id, tenant_id, rule_type, priority, enabled, data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    rule.policy_rule_id, tid,
                    rule.rule_type.value if hasattr(rule.rule_type, "value") else rule.rule_type,
                    rule.priority, int(rule.enabled),
                    _dump(rule),
                ),
            )
        return rule

    def list_policy_rules(self, tenant_id: str) -> list[PolicyRule]:
        """Return rules ordered by descending priority (SPEC_03 §3 evaluation order)."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "rbac_policy_rules", tid, order_by="priority DESC"
            )
        return [PolicyRule.model_validate(json.loads(r["data"])) for r in rows]

    def get_policy_rule(self, tenant_id: str, rule_id: str) -> PolicyRule | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "rbac_policy_rules", tid, "AND policy_rule_id = ?", (rule_id,)
            )
        if row is None:
            return None
        return PolicyRule.model_validate(json.loads(row["data"]))

    def update_policy_rule(self, rule: PolicyRule) -> PolicyRule:
        tid = self._require_tenant_id(rule.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE rbac_policy_rules
                   SET rule_type = ?, priority = ?, enabled = ?, data = ?
                   WHERE tenant_id = ? AND policy_rule_id = ?""",
                (
                    rule.rule_type.value if hasattr(rule.rule_type, "value") else rule.rule_type,
                    rule.priority, int(rule.enabled),
                    _dump(rule),
                    tid, rule.policy_rule_id,
                ),
            )
        return rule

    # ---------------------------------------------------------------- #
    # Authorization decision log (append-only per SPEC_03 §2.6)        #
    # ---------------------------------------------------------------- #

    def log_decision(self, log: AuthorizationDecisionLog) -> None:
        """Append an immutable authorization decision record."""
        tid = self._require_tenant_id(log.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO rbac_decision_logs
                   (decision_id, tenant_id, decision, evaluated_at, data)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    log.decision_id, tid,
                    log.decision,
                    log.evaluated_at.isoformat(),
                    _dump(log),
                ),
            )

    def list_decision_logs(self, tenant_id: str) -> list[AuthorizationDecisionLog]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "rbac_decision_logs", tid, order_by="evaluated_at DESC"
            )
        return [AuthorizationDecisionLog.model_validate(json.loads(r["data"])) for r in rows]
