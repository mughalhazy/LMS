"""SQLite-backed user store — persistent implementation of UserStore and AuditLogStore Protocols.

Tables:
  users           — UserAggregate (Pydantic model, full JSON + key columns)
  user_audit_log  — AuditLogEntry (append-only, Pydantic model)

Architecture anchors:
  ARCH_04 — user-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on every table; tenant-first query pattern.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import AuditLogEntry, UserAggregate


class SQLiteUserStore(BaseRepository):
    """Persistent UserStore backed by SQLite.

    Implements app.store.UserStore Protocol — drop-in replacement for InMemoryUserStore.
    """

    _SERVICE_NAME = "user-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     TEXT NOT NULL,
                    tenant_id   TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'provisioned',
                    version     INTEGER NOT NULL DEFAULT 1,
                    email       TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    deleted_at  TEXT,
                    data        TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_users_email
                    ON users (tenant_id, email);
            """)

    # ---------------------------------------------------------------- #
    # UserStore Protocol                                                 #
    # ---------------------------------------------------------------- #

    def create(self, user: UserAggregate) -> UserAggregate:
        tid = self._require_tenant_id(user.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO users
                   (user_id, tenant_id, status, version, email, created_at, updated_at, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user.user_id, tid,
                    user.status.value,
                    user.version,
                    user.identity.email,
                    user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                    user.model_dump_json(),
                ),
            )
        return user

    def update(self, user: UserAggregate) -> UserAggregate:
        tid = self._require_tenant_id(user.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE users
                   SET status = ?, version = ?, email = ?, updated_at = ?, data = ?
                   WHERE tenant_id = ? AND user_id = ?""",
                (
                    user.status.value,
                    user.version,
                    user.identity.email,
                    user.updated_at.isoformat(),
                    user.model_dump_json(),
                    tid, user.user_id,
                ),
            )
        return user

    def get(self, tenant_id: str, user_id: str) -> UserAggregate | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(conn, "users", tid, "AND user_id = ?", (user_id,))
        if row is None:
            return None
        return UserAggregate.model_validate_json(row["data"])

    def list(self, tenant_id: str) -> list[UserAggregate]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "users", tid)
        return [UserAggregate.model_validate_json(r["data"]) for r in rows]


class SQLiteAuditLogStore(BaseRepository):
    """Persistent AuditLogStore backed by SQLite (append-only).

    Implements app.store.AuditLogStore Protocol.
    """

    _SERVICE_NAME = "user-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_audit_log (
                    audit_id   TEXT PRIMARY KEY,
                    tenant_id  TEXT NOT NULL,
                    user_id    TEXT NOT NULL,
                    action     TEXT NOT NULL,
                    actor_id   TEXT NOT NULL,
                    at         TEXT NOT NULL,
                    data       TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_user_audit_user
                    ON user_audit_log (tenant_id, user_id);
            """)

    # ---------------------------------------------------------------- #
    # AuditLogStore Protocol                                             #
    # ---------------------------------------------------------------- #

    def append(self, entry: AuditLogEntry) -> None:
        tid = self._require_tenant_id(entry.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO user_audit_log (audit_id, tenant_id, user_id, action, actor_id, at, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.audit_id, tid, entry.user_id,
                    entry.action, entry.actor_id,
                    entry.at.isoformat(),
                    entry.model_dump_json(),
                ),
            )

    def list_for_user(self, tenant_id: str, user_id: str) -> list[AuditLogEntry]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "user_audit_log", tid,
                "AND user_id = ?", (user_id,),
                order_by="at ASC",
            )
        return [AuditLogEntry.model_validate_json(r["data"]) for r in rows]
