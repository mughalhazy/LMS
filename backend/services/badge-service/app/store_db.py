"""SQLite-backed badge store — persistent implementation of BadgeRepositoryProtocol.

Tables:
  badge_definitions — BadgeDefinition (tenant-scoped)
  badge_issuances   — BadgeIssuance (tenant-scoped)

Architecture anchors:
  ARCH_04 — badge-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import BadgeDefinition, BadgeIssuance, BadgeIssuanceStatus, BadgeStatus


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


@runtime_checkable
class BadgeRepositoryProtocol(Protocol):
    def create_badge(self, badge: BadgeDefinition) -> BadgeDefinition: ...
    def get_badge(self, badge_id: str, tenant_id: str) -> BadgeDefinition | None: ...
    def list_badges(self, tenant_id: str) -> list[BadgeDefinition]: ...
    def create_issuance(self, issuance: BadgeIssuance) -> BadgeIssuance: ...
    def get_issuance(self, issuance_id: str, tenant_id: str) -> BadgeIssuance | None: ...
    def list_issuances(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        badge_id: str | None = None,
    ) -> list[BadgeIssuance]: ...
    def serialize_badge(self, badge: BadgeDefinition) -> dict: ...
    def serialize_issuance(self, issuance: BadgeIssuance) -> dict: ...


class SQLiteBadgeRepository(BaseRepository):
    """Persistent BadgeRepositoryProtocol backed by SQLite.

    Drop-in replacement for InMemoryBadgeRepository.
    """

    _SERVICE_NAME = "badge-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS badge_definitions (
                    badge_id    TEXT NOT NULL,
                    tenant_id   TEXT NOT NULL,
                    code        TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT NOT NULL,
                    criteria    TEXT NOT NULL DEFAULT '{}',
                    image_url   TEXT,
                    metadata    TEXT NOT NULL DEFAULT '{}',
                    status      TEXT NOT NULL DEFAULT 'active',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, badge_id)
                );
                CREATE INDEX IF NOT EXISTS idx_badge_definitions_tenant
                    ON badge_definitions (tenant_id, status);

                CREATE TABLE IF NOT EXISTS badge_issuances (
                    issuance_id     TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    badge_id        TEXT NOT NULL,
                    learner_id      TEXT NOT NULL,
                    issued_by       TEXT NOT NULL,
                    evidence        TEXT NOT NULL DEFAULT '{}',
                    issued_at       TEXT NOT NULL,
                    status          TEXT NOT NULL DEFAULT 'issued',
                    revoked_at      TEXT,
                    revoke_reason   TEXT,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, issuance_id)
                );
                CREATE INDEX IF NOT EXISTS idx_badge_issuances_learner
                    ON badge_issuances (tenant_id, learner_id);
                CREATE INDEX IF NOT EXISTS idx_badge_issuances_badge
                    ON badge_issuances (tenant_id, badge_id);
            """)

    # ---------------------------------------------------------------- #
    # BadgeRepositoryProtocol — definitions                            #
    # ---------------------------------------------------------------- #

    def create_badge(self, badge: BadgeDefinition) -> BadgeDefinition:
        tid = self._require_tenant_id(badge.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO badge_definitions
                   (badge_id, tenant_id, code, title, description, criteria,
                    image_url, metadata, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    badge.badge_id, tid, badge.code, badge.title, badge.description,
                    json.dumps(badge.criteria), badge.image_url,
                    json.dumps(badge.metadata), badge.status.value,
                    _iso(badge.created_at), _iso(badge.updated_at),
                ),
            )
        return badge

    def get_badge(self, badge_id: str, tenant_id: str) -> BadgeDefinition | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "badge_definitions", tid, "AND badge_id = ?", (badge_id,)
            )
        return _row_to_badge(dict(row)) if row else None

    def list_badges(self, tenant_id: str) -> list[BadgeDefinition]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "badge_definitions", tid, order_by="created_at ASC"
            )
        return [_row_to_badge(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # BadgeRepositoryProtocol — issuances                              #
    # ---------------------------------------------------------------- #

    def create_issuance(self, issuance: BadgeIssuance) -> BadgeIssuance:
        tid = self._require_tenant_id(issuance.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO badge_issuances
                   (issuance_id, tenant_id, badge_id, learner_id, issued_by, evidence,
                    issued_at, status, revoked_at, revoke_reason, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    issuance.issuance_id, tid, issuance.badge_id, issuance.learner_id,
                    issuance.issued_by, json.dumps(issuance.evidence),
                    _iso(issuance.issued_at), issuance.status.value,
                    _iso(issuance.revoked_at), issuance.revoke_reason,
                    _iso(issuance.created_at), _iso(issuance.updated_at),
                ),
            )
        return issuance

    def get_issuance(self, issuance_id: str, tenant_id: str) -> BadgeIssuance | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "badge_issuances", tid, "AND issuance_id = ?", (issuance_id,)
            )
        return _row_to_issuance(dict(row)) if row else None

    def list_issuances(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        badge_id: str | None = None,
    ) -> list[BadgeIssuance]:
        tid = self._require_tenant_id(tenant_id)
        extra_sql = ""
        extra_params: list = []
        if learner_id:
            extra_sql += " AND learner_id = ?"
            extra_params.append(learner_id)
        if badge_id:
            extra_sql += " AND badge_id = ?"
            extra_params.append(badge_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "badge_issuances", tid,
                extra_sql or None, tuple(extra_params) if extra_params else None,
                order_by="issued_at ASC",
            )
        return [_row_to_issuance(dict(r)) for r in rows]

    # ---------------------------------------------------------------- #
    # Serialisation helpers (mirrors InMemoryBadgeRepository)          #
    # ---------------------------------------------------------------- #

    def serialize_badge(self, badge: BadgeDefinition) -> dict:
        return asdict(badge)

    def serialize_issuance(self, issuance: BadgeIssuance) -> dict:
        return asdict(issuance)


# ---------------------------------------------------------------- #
# Deserialisation helpers                                           #
# ---------------------------------------------------------------- #

def _row_to_badge(r: dict) -> BadgeDefinition:
    return BadgeDefinition(
        badge_id=r["badge_id"],
        tenant_id=r["tenant_id"],
        code=r["code"],
        title=r["title"],
        description=r["description"],
        criteria=json.loads(r["criteria"]),
        image_url=r.get("image_url"),
        metadata=json.loads(r["metadata"]),
        status=BadgeStatus(r["status"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )


def _row_to_issuance(r: dict) -> BadgeIssuance:
    return BadgeIssuance(
        issuance_id=r["issuance_id"],
        tenant_id=r["tenant_id"],
        badge_id=r["badge_id"],
        learner_id=r["learner_id"],
        issued_by=r["issued_by"],
        evidence=json.loads(r["evidence"]),
        issued_at=datetime.fromisoformat(r["issued_at"]),
        status=BadgeIssuanceStatus(r["status"]),
        revoked_at=_dt(r.get("revoked_at")),
        revoke_reason=r.get("revoke_reason"),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )
