"""SQLite-backed auth store — persistent replacement for InMemoryAuthStore.

Implements AuthStoreProtocol; service.py can inject either implementation.

Tables (per auth_service_storage_contract.md + practical credential need):
  auth_tenants                    — local tenant cache (referenced by FK)
  auth_user_credentials           — password hash + roles (auth ownership)
  auth_sessions                   — active / revoked session records
  auth_refresh_tokens             — refresh token chain with rotation links
  auth_password_reset_challenges  — one-time reset tokens
  auth_audit_log                  — immutable append-only audit trail
  auth_outbox_events              — transactional outbox for domain events

Architecture anchors:
  ARCH_04 — service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tenant-owned tables;
             tenant-first query pattern via BaseRepository helpers.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import ResetChallenge, Session, Tenant, UserCredential


# ──────────────────────────────────────────────────────────────────── #
# Tenant lookup proxy (compatibility with store.tenants.get() pattern) #
# ──────────────────────────────────────────────────────────────────── #

class _TenantLookup:
    """Dict-like proxy over auth_tenants table.

    Keeps service.py's ``store.tenants.get(req.tenant_id)`` call unchanged.
    """

    def __init__(self, store: "SQLiteAuthStore") -> None:
        self._store = store

    def get(self, tenant_id: str, default: object = None) -> Optional[Tenant]:
        if not tenant_id:
            return default  # type: ignore[return-value]
        with self._store._connect() as conn:
            row = conn.execute(
                "SELECT tenant_id, name, active FROM auth_tenants WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            ).fetchone()
        if row is None:
            return default  # type: ignore[return-value]
        return Tenant(tenant_id=row["tenant_id"], name=row["name"], active=bool(row["active"]))


# ──────────────────────────────────────────────────────────────────── #
# Protocol                                                             #
# ──────────────────────────────────────────────────────────────────── #

@runtime_checkable
class AuthStoreProtocol(Protocol):
    """Structural contract shared by InMemoryAuthStore and SQLiteAuthStore.

    Service code type-annotates against this protocol to remain storage-agnostic.
    """

    tenants: _TenantLookup

    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[UserCredential]: ...
    def save_session(self, user_id: str, tenant_id: str, access_ttl_s: int, refresh_ttl_s: int) -> Session: ...
    def get_session(self, session_id: str) -> Optional[Session]: ...
    def revoke_session(self, session_id: str) -> None: ...
    def create_reset_challenge(self, user_id: str, tenant_id: str, ttl_seconds: int) -> ResetChallenge: ...
    def get_reset_challenge(self, token: str) -> Optional[ResetChallenge]: ...
    def update_password(self, tenant_id: str, email: str, new_password_hash: str) -> bool: ...


# ──────────────────────────────────────────────────────────────────── #
# SQLite store                                                         #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteAuthStore(BaseRepository):
    """Persistent, tenant-isolated auth store backed by SQLite.

    Usage::

        store = SQLiteAuthStore()          # uses ./data/auth-service.db
        store = SQLiteAuthStore(db_path)   # explicit path (e.g. tests)
    """

    _SERVICE_NAME = "auth-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))
        self.tenants: _TenantLookup = _TenantLookup(self)

    # ---------------------------------------------------------------- #
    # Schema (ARCH_07: tenant_id NOT NULL on every tenant-owned table)  #
    # ---------------------------------------------------------------- #

    def _init_schema(self) -> None:
        statements = [
            # Tenant cache — referenced by FKs; populated by tenant-service events
            """CREATE TABLE IF NOT EXISTS auth_tenants (
                tenant_id  TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                active     INTEGER NOT NULL DEFAULT 1
            )""",
            # Auth-service owns user credentials (password hashes, roles list)
            """CREATE TABLE IF NOT EXISTS auth_user_credentials (
                user_id         TEXT NOT NULL,
                tenant_id       TEXT NOT NULL,
                organization_id TEXT,
                email           TEXT NOT NULL,
                password_hash   TEXT NOT NULL,
                roles           TEXT NOT NULL DEFAULT '[]',
                status          TEXT NOT NULL DEFAULT 'active',
                last_login_at   TEXT,
                PRIMARY KEY (tenant_id, email),
                FOREIGN KEY (tenant_id) REFERENCES auth_tenants(tenant_id)
            )""",
            # auth_service_storage_contract.md — auth_sessions
            """CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id         TEXT PRIMARY KEY,
                tenant_id          TEXT NOT NULL,
                user_id            TEXT NOT NULL,
                state              TEXT NOT NULL DEFAULT 'active',
                auth_method        TEXT,
                assurance_level    TEXT,
                issued_at          TEXT NOT NULL,
                expires_at         TEXT NOT NULL,
                refresh_expires_at TEXT,
                last_seen_at       TEXT,
                revoked_at         TEXT,
                revoked_reason     TEXT
            )""",
            # auth_service_storage_contract.md — auth_refresh_tokens
            """CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                token_id             TEXT PRIMARY KEY,
                tenant_id            TEXT NOT NULL,
                user_id              TEXT,
                session_id           TEXT,
                parent_token_id      TEXT,
                replaced_by_token_id TEXT,
                token_fingerprint    TEXT UNIQUE NOT NULL,
                hashed_secret        TEXT NOT NULL,
                issued_at            TEXT NOT NULL,
                expires_at           TEXT NOT NULL,
                used_at              TEXT,
                revoked_at           TEXT,
                FOREIGN KEY (session_id) REFERENCES auth_sessions(session_id)
            )""",
            # auth_service_storage_contract.md — auth_password_reset_challenges
            """CREATE TABLE IF NOT EXISTS auth_password_reset_challenges (
                challenge_id     TEXT PRIMARY KEY,
                tenant_id        TEXT NOT NULL,
                user_id          TEXT NOT NULL,
                challenge_hash   TEXT NOT NULL,
                delivery_channel TEXT,
                requested_at     TEXT NOT NULL,
                expires_at       TEXT NOT NULL,
                consumed_at      TEXT,
                attempt_count    INTEGER NOT NULL DEFAULT 0,
                max_attempts     INTEGER NOT NULL DEFAULT 5
            )""",
            # auth_service_storage_contract.md — auth_audit_log (append-only)
            """CREATE TABLE IF NOT EXISTS auth_audit_log (
                event_id        TEXT PRIMARY KEY,
                tenant_id       TEXT NOT NULL,
                event_type      TEXT NOT NULL,
                severity        TEXT,
                actor_user_id   TEXT,
                subject_user_id TEXT,
                session_id      TEXT,
                result          TEXT,
                reason_code     TEXT,
                correlation_id  TEXT,
                trace_id        TEXT,
                metadata        TEXT,
                timestamp       TEXT NOT NULL
            )""",
            # auth_service_storage_contract.md — auth_outbox_events
            """CREATE TABLE IF NOT EXISTS auth_outbox_events (
                outbox_id    TEXT PRIMARY KEY,
                event_id     TEXT UNIQUE NOT NULL,
                event_type   TEXT NOT NULL,
                tenant_id    TEXT NOT NULL,
                payload      TEXT NOT NULL,
                published_at TEXT,
                attempts     INTEGER NOT NULL DEFAULT 0
            )""",
        ]
        with self._connect() as conn:
            for stmt in statements:
                conn.execute(stmt)

    # ---------------------------------------------------------------- #
    # Tenant registration (for test setup / provisioning events)        #
    # ---------------------------------------------------------------- #

    def register_tenant(self, tenant_id: str, name: str, active: bool = True) -> None:
        """Upsert a tenant record into the local cache."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_tenants (tenant_id, name, active)
                   VALUES (?, ?, ?)
                   ON CONFLICT(tenant_id) DO UPDATE SET name=excluded.name, active=excluded.active""",
                (tenant_id, name, int(active)),
            )

    def register_user(self, credential: UserCredential) -> None:
        """Upsert a user credential record (used for seeding and provisioning)."""
        tid = self._require_tenant_id(credential.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_user_credentials
                   (user_id, tenant_id, organization_id, email, password_hash, roles, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, email) DO UPDATE SET
                     password_hash=excluded.password_hash,
                     roles=excluded.roles,
                     status=excluded.status""",
                (
                    credential.user_id, tid,
                    credential.organization_id,
                    credential.email.lower(),
                    credential.password_hash,
                    json.dumps(credential.roles),
                    credential.status,
                ),
            )

    # ---------------------------------------------------------------- #
    # Credential methods                                                 #
    # ---------------------------------------------------------------- #

    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[UserCredential]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "auth_user_credentials", tid,
                "AND email = ?", (email.lower(),),
            )
        if row is None:
            return None
        return UserCredential(
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            organization_id=row["organization_id"] or "",
            email=row["email"],
            password_hash=row["password_hash"],
            roles=json.loads(row["roles"]),
            status=row["status"],
            last_login_at=(
                datetime.fromisoformat(row["last_login_at"])
                if row["last_login_at"] else None
            ),
        )

    def update_password(self, tenant_id: str, email: str, new_password_hash: str) -> bool:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE auth_user_credentials
                   SET password_hash = ?
                   WHERE tenant_id = ? AND email = ?""",
                (new_password_hash, tid, email.lower()),
            )
        return cursor.rowcount > 0

    # ---------------------------------------------------------------- #
    # Session methods                                                    #
    # ---------------------------------------------------------------- #

    def save_session(
        self,
        user_id: str,
        tenant_id: str,
        access_ttl_s: int,
        refresh_ttl_s: int,
    ) -> Session:
        """Create and persist a new session. ARCH_07: tenant_id validated first."""
        tid = self._require_tenant_id(tenant_id)
        now = datetime.now(timezone.utc)
        session = Session(
            session_id=secrets.token_urlsafe(24),
            user_id=user_id,
            tenant_id=tid,
            issued_at=now,
            expires_at=now + timedelta(seconds=access_ttl_s),
            refresh_expires_at=now + timedelta(seconds=refresh_ttl_s),
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_sessions
                   (session_id, tenant_id, user_id, state, issued_at, expires_at, refresh_expires_at)
                   VALUES (?, ?, ?, 'active', ?, ?, ?)""",
                (
                    session.session_id, tid, user_id,
                    session.issued_at.isoformat(),
                    session.expires_at.isoformat(),
                    session.refresh_expires_at.isoformat(),
                ),
            )
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Fetch session by ID. Note: session_id is globally unique — no tenant scope needed here."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM auth_sessions WHERE session_id = ? LIMIT 1",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        refresh_exp = (
            datetime.fromisoformat(row["refresh_expires_at"])
            if row["refresh_expires_at"]
            else datetime.fromisoformat(row["expires_at"])
        )
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            issued_at=datetime.fromisoformat(row["issued_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            refresh_expires_at=refresh_exp,
            revoked=row["state"] == "revoked",
        )

    def revoke_session(self, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE auth_sessions
                   SET state = 'revoked', revoked_at = ?
                   WHERE session_id = ?""",
                (now, session_id),
            )

    # ---------------------------------------------------------------- #
    # Refresh tokens                                                     #
    # ---------------------------------------------------------------- #

    def create_refresh_token(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        hashed_secret: str,
        token_fingerprint: str,
        ttl_seconds: int,
        parent_token_id: str | None = None,
    ) -> str:
        """Issue a new refresh token. Returns token_id."""
        tid = self._require_tenant_id(tenant_id)
        token_id = secrets.token_urlsafe(16)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_refresh_tokens
                   (token_id, tenant_id, user_id, session_id, parent_token_id,
                    token_fingerprint, hashed_secret, issued_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    token_id, tid, user_id, session_id, parent_token_id,
                    token_fingerprint, hashed_secret,
                    now.isoformat(), expires_at.isoformat(),
                ),
            )
        return token_id

    def get_refresh_token_by_fingerprint(self, fingerprint: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM auth_refresh_tokens WHERE token_fingerprint = ? LIMIT 1",
                (fingerprint,),
            ).fetchone()
        return self._row(row)

    def rotate_refresh_token(self, old_token_id: str, new_token_id: str) -> None:
        """Mark old token as replaced; used_at is set."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE auth_refresh_tokens
                   SET replaced_by_token_id = ?, used_at = ?
                   WHERE token_id = ?""",
                (new_token_id, now, old_token_id),
            )

    # ---------------------------------------------------------------- #
    # Password reset challenges                                          #
    # ---------------------------------------------------------------- #

    def create_reset_challenge(
        self,
        user_id: str,
        tenant_id: str,
        ttl_seconds: int = 900,
    ) -> ResetChallenge:
        tid = self._require_tenant_id(tenant_id)
        now = datetime.now(timezone.utc)
        challenge = ResetChallenge(
            challenge_id=secrets.token_urlsafe(12),
            user_id=user_id,
            tenant_id=tid,
            token=secrets.token_urlsafe(32),
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_password_reset_challenges
                   (challenge_id, tenant_id, user_id, challenge_hash, requested_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    challenge.challenge_id, tid, user_id,
                    challenge.token,
                    now.isoformat(),
                    challenge.expires_at.isoformat(),
                ),
            )
        return challenge

    def get_reset_challenge(self, token: str) -> Optional[ResetChallenge]:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM auth_password_reset_challenges
                   WHERE challenge_hash = ? LIMIT 1""",
                (token,),
            ).fetchone()
        if row is None:
            return None
        return ResetChallenge(
            challenge_id=row["challenge_id"],
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            token=row["challenge_hash"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            used=row["consumed_at"] is not None,
        )

    def consume_reset_challenge(self, challenge_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE auth_password_reset_challenges
                   SET consumed_at = ?, attempt_count = attempt_count + 1
                   WHERE challenge_id = ?""",
                (now, challenge_id),
            )

    # ---------------------------------------------------------------- #
    # Audit log (append-only per auth_service_storage_contract.md)      #
    # ---------------------------------------------------------------- #

    def append_audit_event(
        self,
        tenant_id: str,
        event_type: str,
        *,
        event_id: str | None = None,
        severity: str = "info",
        actor_user_id: str | None = None,
        subject_user_id: str | None = None,
        session_id: str | None = None,
        result: str | None = None,
        reason_code: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Append an immutable audit event. Returns event_id."""
        tid = self._require_tenant_id(tenant_id)
        eid = event_id or secrets.token_urlsafe(16)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_audit_log
                   (event_id, tenant_id, event_type, severity, actor_user_id, subject_user_id,
                    session_id, result, reason_code, correlation_id, trace_id, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    eid, tid, event_type, severity,
                    actor_user_id, subject_user_id, session_id,
                    result, reason_code, correlation_id, trace_id,
                    json.dumps(metadata or {}),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return eid

    def list_audit_events(self, tenant_id: str, limit: int = 100) -> list[dict]:
        """Retrieve audit events for a tenant, newest first."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(
                conn, "auth_audit_log", tid,
                order_by="timestamp DESC",
            )
        return self._rows(rows[:limit])

    # ---------------------------------------------------------------- #
    # Outbox events (transactional outbox pattern)                      #
    # ---------------------------------------------------------------- #

    def enqueue_outbox_event(self, tenant_id: str, event_type: str, payload: dict) -> str:
        """Add an event to the transactional outbox. Returns outbox_id."""
        tid = self._require_tenant_id(tenant_id)
        outbox_id = secrets.token_urlsafe(16)
        event_id = secrets.token_urlsafe(16)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO auth_outbox_events
                   (outbox_id, event_id, event_type, tenant_id, payload)
                   VALUES (?, ?, ?, ?, ?)""",
                (outbox_id, event_id, event_type, tid, json.dumps(payload)),
            )
        return outbox_id

    def claim_outbox_events(self, tenant_id: str, limit: int = 50) -> list[dict]:
        """Return unpublished outbox events for relay, oldest first."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM auth_outbox_events
                   WHERE tenant_id = ? AND published_at IS NULL
                   ORDER BY outbox_id LIMIT ?""",
                (tid, limit),
            ).fetchall()
        return self._rows(rows)

    def mark_outbox_published(self, outbox_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE auth_outbox_events
                   SET published_at = ?, attempts = attempts + 1
                   WHERE outbox_id = ?""",
                (now, outbox_id),
            )
