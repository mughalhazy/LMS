"""Shared persistence infrastructure — stdlib sqlite3, no external dependencies.

Architecture anchors:
  ARCH_04 §Security Isolation
    "Each service has isolated credentials and least-privilege access limited to
    its own datastore."
    Enforced by: resolve_db_path() returns a service-specific file; BaseRepository
    never shares a db_path across services.

  ARCH_07 §2 Persistence Boundary
    "Every tenant-owned table includes tenant_id NOT NULL."
    "Query pattern: include tenant_id predicate first, then entity predicate."
    "Composite uniqueness must include tenant scope."
    Enforced by:
      _require_tenant_id()  — validates tenant_id is non-empty on every op
      _q()                  — tenant-first SELECT / UPDATE / DELETE helpers
      Schema convention     — all CREATE TABLE templates include tenant_id NOT NULL

  ARCH_07 §6 API Isolation
    "Resource IDs are never trusted alone; all fetches are (tenant_id, resource_id)."
    Enforced by: _fetch_one() and _fetch_all() always prepend tenant_id to WHERE.

  Precedent: content-service/content_service/repository.py uses the same pattern
    (stdlib sqlite3, row_factory, CREATE TABLE IF NOT EXISTS).
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ #
# Path resolution                                                      #
# ------------------------------------------------------------------ #

def resolve_db_path(service_name: str) -> Path:
    """Return the canonical SQLite file path for a service.

    Resolution order (ARCH_04 — per-service isolation):
      1. {SERVICE_NAME_UPPER}_DATABASE_PATH env var   (service-specific override)
      2. DATABASE_PATH env var                         (shared test override)
      3. default → ./data/{service_name}.db

    The data/ directory is created on first call (idempotent).

    Examples
    --------
    >>> resolve_db_path("auth-service")   # → ./data/auth-service.db
    >>> resolve_db_path("enrollment-be")  # → ./data/enrollment-be.db
    """
    env_key = f"{service_name.upper().replace('-', '_')}_DATABASE_PATH"
    raw = os.getenv(env_key) or os.getenv("DATABASE_PATH") or f"./data/{service_name}.db"
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ------------------------------------------------------------------ #
# Connection factory                                                   #
# ------------------------------------------------------------------ #

def connect(db_path: Path | str) -> sqlite3.Connection:
    """Open a sqlite3 connection tuned for service use.

    Settings applied:
      row_factory = sqlite3.Row   — dict-like row access (.keys(), indexing)
      journal_mode = WAL          — concurrent reads without blocking writes
      foreign_keys = ON           — enforce FK constraints (ARCH_04 ownership)
      busy_timeout = 5000 ms      — retry on locked DB instead of failing immediately

    Usage (follows content-service precedent):
        with connect(db_path) as conn:
            conn.execute("INSERT INTO ...")
        # auto-commits on __exit__, rolls back on exception
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ------------------------------------------------------------------ #
# Base repository mixin                                                #
# ------------------------------------------------------------------ #

class BaseRepository:
    """Mixin base class for all DB-backed store implementations.

    Contract (must be honoured by every subclass):

    ARCH_04 — per-service isolation:
      - Pass a service-specific db_path; never share across services.
      - _init_schema() creates all tables with CREATE TABLE IF NOT EXISTS.

    ARCH_07 — tenant isolation at the DB layer:
      - All table DDL must include tenant_id TEXT NOT NULL (enforced by convention).
      - _require_tenant_id() must be called at the top of every public method.
      - _fetch_one() / _fetch_all() always include tenant_id as the FIRST predicate.
      - _execute_tenant() validates tenant_id before any DML.

    Usage pattern (mirrors content-service repository):
        class MySQLiteStore(BaseRepository):
            _SERVICE_NAME = "my-service"

            def __init__(self, db_path=None):
                super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

            def _init_schema(self):
                with self._connect() as conn:
                    conn.execute(
                        \"\"\"CREATE TABLE IF NOT EXISTS my_table (
                            id TEXT PRIMARY KEY,
                            tenant_id TEXT NOT NULL,
                            ...
                        )\"\"\"
                    )
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ---- connection ---- #

    def _connect(self) -> sqlite3.Connection:
        """Return a connection to this service's isolated DB file."""
        return connect(self._db_path)

    # ---- schema ---- #

    def _init_schema(self) -> None:
        """Subclasses create tables here with CREATE TABLE IF NOT EXISTS."""

    # ---- ARCH_07 tenant enforcement ---- #

    def _require_tenant_id(self, tenant_id: str) -> str:
        """Validate tenant_id is present. ARCH_07: required on every op.

        Raises ValueError for empty/None — prevents silent cross-tenant leakage.
        """
        if not tenant_id or not str(tenant_id).strip():
            raise ValueError(
                "tenant_id is required on every read/write operation (ARCH_07 §2). "
                "Resource IDs alone are never sufficient to scope a query."
            )
        return str(tenant_id).strip()

    # ---- tenant-first query helpers (ARCH_07) ---- #

    def _fetch_one(
        self,
        conn: sqlite3.Connection,
        table: str,
        tenant_id: str,
        extra_where: str = "",
        params: tuple[Any, ...] = (),
        columns: str = "*",
    ) -> sqlite3.Row | None:
        """SELECT with tenant_id as the FIRST predicate.

        ARCH_07: "Query pattern for reads: include tenant_id predicate first,
        then entity predicate."

        Example:
            row = self._fetch_one(conn, "enrollments", tenant_id,
                                  "AND enrollment_id = ?", (eid,))
        """
        tid = self._require_tenant_id(tenant_id)
        where = f"WHERE tenant_id = ?{' ' + extra_where if extra_where else ''}"
        sql = f"SELECT {columns} FROM {table} {where} LIMIT 1"
        cursor = conn.execute(sql, (tid, *params))
        return cursor.fetchone()

    def _fetch_all(
        self,
        conn: sqlite3.Connection,
        table: str,
        tenant_id: str,
        extra_where: str = "",
        params: tuple[Any, ...] = (),
        columns: str = "*",
        order_by: str = "",
    ) -> list[sqlite3.Row]:
        """SELECT * with tenant_id as the FIRST predicate.

        ARCH_07: tenant predicate always first; optional filters appended after.
        """
        tid = self._require_tenant_id(tenant_id)
        where = f"WHERE tenant_id = ?{' ' + extra_where if extra_where else ''}"
        order = f"ORDER BY {order_by}" if order_by else ""
        sql = f"SELECT {columns} FROM {table} {where} {order}".strip()
        cursor = conn.execute(sql, (tid, *params))
        return cursor.fetchall()

    def _execute_tenant(
        self,
        conn: sqlite3.Connection,
        sql: str,
        tenant_id: str,
        params: tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        """Execute a DML statement after validating tenant_id.

        ARCH_07: tenant_id validated before any INSERT/UPDATE/DELETE.
        The tenant_id value is injected as the first positional parameter.
        """
        tid = self._require_tenant_id(tenant_id)
        return conn.execute(sql, (tid, *params))

    # ---- serialisation helpers ---- #

    def _row(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        """Convert sqlite3.Row to plain dict, or None."""
        return dict(row) if row is not None else None

    def _rows(self, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        """Convert list of sqlite3.Row to list of plain dicts."""
        return [dict(r) for r in rows]
