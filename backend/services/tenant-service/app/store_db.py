"""SQLite-backed tenant store — persistent implementation of TenantStore Protocol.

Implements app.store.TenantStore; service.py can inject either implementation.

Tables (per SPEC_04 §3 — 5 owned entities, mapped to models.py dataclasses):
  tenants                     — Tenant root record (SPEC_04 §3.1.1)
  tenant_namespaces           — TenantNamespace resource locator (app.models)
  tenant_lifecycle_events     — LifecycleEvent history (SPEC_04 §3.1.2)
  tenant_configurations       — TenantConfiguration versioned payload (SPEC_04 §3.1.3)
  tenant_plan_links           — plan linkage metadata (SPEC_04 §3.1.4)
  tenant_isolation_policies   — isolation policy descriptor (SPEC_04 §3.1.5)

Architecture anchors:
  ARCH_04 — tenant-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on all tables; tenant-first query pattern.
  SPEC_04 §3.3 — source of truth for tenant root identity, status, config
                 versions, plan links, and isolation metadata.
  SPEC_04 §3.1.1 — tenant_key is the external-friendly unique identifier;
                   maps to TenantStore.by_code(tenant_code) lookup.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    IsolationMode,
    LifecycleEvent,
    LifecycleState,
    Tenant,
    TenantConfiguration,
    TenantNamespace,
)


# ──────────────────────────────────────────────────────────────────── #
# Serialisation helpers for dataclass models                           #
# ──────────────────────────────────────────────────────────────────── #

def _dump_json(obj) -> str:
    """JSON-serialise a dataclass or dict, converting datetimes to ISO strings."""
    def _default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "value"):          # Enum
            return o.value
        raise TypeError(f"Not serialisable: {type(o)}")

    if hasattr(obj, "__dataclass_fields__"):
        return json.dumps(asdict(obj), default=_default)
    return json.dumps(obj, default=_default)


def _load_tenant(row: dict) -> Tenant:
    """Reconstruct a Tenant dataclass from a DB row dict."""
    config_raw = row.get("configuration") or "{}"
    config_dict = json.loads(config_raw)

    configuration = TenantConfiguration(
        version=config_dict.get("version", 1),
        default_locale=config_dict.get("default_locale", "en-US"),
        timezone=config_dict.get("timezone", "UTC"),
        branding=config_dict.get("branding", {}),
        enabled_modules=config_dict.get("enabled_modules", []),
        security_baseline=config_dict.get("security_baseline", {}),
        feature_flags=config_dict.get("feature_flags", {}),
        country_behavior_profiles=config_dict.get("country_behavior_profiles", {}),
    )

    history_raw = row.get("state_history") or "[]"
    history = []
    for ev in json.loads(history_raw):
        history.append(LifecycleEvent(
            state=LifecycleState(ev["state"]),
            reason=ev["reason"],
            actor_id=ev["actor_id"],
            effective_at=datetime.fromisoformat(ev["effective_at"]),
            recorded_at=datetime.fromisoformat(ev["recorded_at"]),
        ))

    return Tenant(
        tenant_id=row["tenant_id"],
        name=row["name"],
        country_code=row["country_code"],
        segment_type=row["segment_type"],
        plan_type=row["plan_type"],
        addon_flags=json.loads(row.get("addon_flags") or "[]"),
        isolation_mode=IsolationMode(row["isolation_mode"]),
        lifecycle_state=LifecycleState(row["lifecycle_state"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        configuration=configuration,
        state_history=history,
    )


# ──────────────────────────────────────────────────────────────────── #
# SQLite store                                                         #
# ──────────────────────────────────────────────────────────────────── #

class SQLiteTenantStore(BaseRepository):
    """Persistent, tenant-isolated store implementing app.store.TenantStore Protocol.

    Usage::

        store = SQLiteTenantStore()           # ./data/tenant-service.db
        store = SQLiteTenantStore(db_path)    # explicit path (tests)

    The service.py wires this via::

        from app.store_db import SQLiteTenantStore
        store: TenantStore = SQLiteTenantStore()
    """

    _SERVICE_NAME = "tenant-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    # ---------------------------------------------------------------- #
    # Schema (SPEC_04 §3 — 5 entities + namespace table)               #
    # ---------------------------------------------------------------- #

    def _init_schema(self) -> None:
        statements = [
            # SPEC_04 §3.1.1 — tenant root record
            # tenant_key: external-friendly slug/identifier; maps to by_code() lookup.
            # ARCH_07: tenant_id is PK (no separate FK needed — this IS the root table).
            """CREATE TABLE IF NOT EXISTS tenants (
                tenant_id       TEXT PRIMARY KEY,
                tenant_key      TEXT UNIQUE,
                name            TEXT NOT NULL,
                country_code    TEXT NOT NULL DEFAULT '',
                segment_type    TEXT NOT NULL DEFAULT '',
                plan_type       TEXT NOT NULL DEFAULT '',
                addon_flags     TEXT NOT NULL DEFAULT '[]',
                isolation_mode  TEXT NOT NULL,
                lifecycle_state TEXT NOT NULL DEFAULT 'provisioning',
                configuration   TEXT NOT NULL DEFAULT '{}',
                state_history   TEXT NOT NULL DEFAULT '[]',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            )""",
            # TenantNamespace (app.models) — resource locator per tenant
            """CREATE TABLE IF NOT EXISTS tenant_namespaces (
                tenant_id        TEXT PRIMARY KEY,
                resource_locator TEXT NOT NULL,
                created_at       TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )""",
            # SPEC_04 §3.1.2 — lifecycle transition history (append-only)
            """CREATE TABLE IF NOT EXISTS tenant_lifecycle_events (
                event_id        TEXT PRIMARY KEY,
                tenant_id       TEXT NOT NULL,
                from_state      TEXT,
                to_state        TEXT NOT NULL,
                reason          TEXT,
                actor_id        TEXT,
                effective_at    TEXT NOT NULL,
                recorded_at     TEXT NOT NULL
            )""",
            # SPEC_04 §3.1.3 — versioned configuration snapshots (append-only)
            """CREATE TABLE IF NOT EXISTS tenant_configurations (
                tenant_id      TEXT NOT NULL,
                config_version INTEGER NOT NULL,
                config_payload TEXT NOT NULL,
                change_summary TEXT,
                changed_by     TEXT,
                changed_at     TEXT NOT NULL,
                PRIMARY KEY (tenant_id, config_version)
            )""",
            # SPEC_04 §3.1.4 — plan linkage
            """CREATE TABLE IF NOT EXISTS tenant_plan_links (
                tenant_id    TEXT NOT NULL,
                plan_id      TEXT NOT NULL,
                plan_version TEXT,
                effective_from TEXT,
                effective_to   TEXT,
                link_status  TEXT NOT NULL DEFAULT 'active',
                updated_by   TEXT,
                updated_at   TEXT NOT NULL,
                PRIMARY KEY (tenant_id, plan_id)
            )""",
            # SPEC_04 §3.1.5 — isolation policy descriptor
            """CREATE TABLE IF NOT EXISTS tenant_isolation_policies (
                tenant_id                TEXT PRIMARY KEY,
                partition_key            TEXT,
                residency_constraints    TEXT,
                encryption_profile_ref   TEXT,
                cross_tenant_access_policy TEXT NOT NULL DEFAULT 'deny',
                policy_version           INTEGER NOT NULL DEFAULT 1,
                updated_at               TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )""",
        ]
        with self._connect() as conn:
            for stmt in statements:
                conn.execute(stmt)

    # ---------------------------------------------------------------- #
    # TenantStore Protocol — core methods                               #
    # ---------------------------------------------------------------- #

    def add(self, tenant: Tenant, namespace: TenantNamespace) -> None:
        """Persist a new tenant + its namespace atomically.

        ARCH_07: tenant_id is the partition root; all downstream tables reference it.
        """
        tid = self._require_tenant_id(tenant.tenant_id)
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tenants
                   (tenant_id, tenant_key, name, country_code, segment_type, plan_type,
                    addon_flags, isolation_mode, lifecycle_state, configuration, state_history,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid,
                    tid,   # tenant_key defaults to tenant_id; callers may override via update()
                    tenant.name,
                    tenant.country_code,
                    tenant.segment_type,
                    tenant.plan_type,
                    json.dumps(tenant.addon_flags),
                    tenant.isolation_mode.value,
                    tenant.lifecycle_state.value,
                    _dump_json(tenant.configuration),
                    _dump_json(tenant.state_history),
                    tenant.created_at.isoformat(),
                    tenant.updated_at.isoformat(),
                ),
            )
            conn.execute(
                """INSERT INTO tenant_namespaces (tenant_id, resource_locator, created_at)
                   VALUES (?, ?, ?)""",
                (tid, namespace.resource_locator, namespace.created_at.isoformat()),
            )

    def update(self, tenant: Tenant) -> None:
        """Persist updated tenant state including lifecycle_state and configuration."""
        tid = self._require_tenant_id(tenant.tenant_id)
        with self._connect() as conn:
            conn.execute(
                """UPDATE tenants SET
                   name = ?, country_code = ?, segment_type = ?, plan_type = ?,
                   addon_flags = ?, isolation_mode = ?, lifecycle_state = ?,
                   configuration = ?, state_history = ?, updated_at = ?
                   WHERE tenant_id = ?""",
                (
                    tenant.name, tenant.country_code, tenant.segment_type, tenant.plan_type,
                    json.dumps(tenant.addon_flags),
                    tenant.isolation_mode.value,
                    tenant.lifecycle_state.value,
                    _dump_json(tenant.configuration),
                    _dump_json(tenant.state_history),
                    datetime.now(timezone.utc).isoformat(),
                    tid,
                ),
            )

    def get(self, tenant_id: str) -> Tenant | None:
        """Fetch tenant by primary key (ARCH_07 §6: resource ID alone is sufficient here
        because tenant IS the root partition key — no parent scope to validate against)."""
        if not tenant_id or not str(tenant_id).strip():
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tenants WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            ).fetchone()
        if row is None:
            return None
        return _load_tenant(dict(row))

    def by_code(self, tenant_code: str) -> Tenant | None:
        """Fetch tenant by external key (SPEC_04 §3.1.1 tenant_key field)."""
        if not tenant_code:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tenants WHERE tenant_key = ? LIMIT 1",
                (tenant_code,),
            ).fetchone()
        if row is None:
            return None
        return _load_tenant(dict(row))

    def namespace_for(self, tenant_id: str) -> TenantNamespace | None:
        """Return the TenantNamespace for this tenant."""
        if not tenant_id:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tenant_namespaces WHERE tenant_id = ? LIMIT 1",
                (tenant_id,),
            ).fetchone()
        if row is None:
            return None
        return TenantNamespace(
            resource_locator=row["resource_locator"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ---------------------------------------------------------------- #
    # SPEC_04 extended methods (beyond TenantStore Protocol)            #
    # ---------------------------------------------------------------- #

    def record_lifecycle_transition(
        self,
        tenant_id: str,
        from_state: str | None,
        to_state: str,
        reason: str,
        actor_id: str,
        effective_at: datetime | None = None,
    ) -> str:
        """Append a lifecycle transition record. Returns event_id."""
        import secrets
        tid = self._require_tenant_id(tenant_id)
        event_id = secrets.token_urlsafe(12)
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tenant_lifecycle_events
                   (event_id, tenant_id, from_state, to_state, reason, actor_id, effective_at, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id, tid, from_state, to_state, reason, actor_id,
                    (effective_at or now).isoformat(),
                    now.isoformat(),
                ),
            )
        return event_id

    def save_configuration_version(
        self,
        tenant_id: str,
        config_version: int,
        config_payload: dict,
        change_summary: str | None = None,
        changed_by: str | None = None,
    ) -> None:
        """Append a versioned configuration snapshot (SPEC_04 §3.1.3)."""
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO tenant_configurations
                   (tenant_id, config_version, config_payload, change_summary, changed_by, changed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    tid, config_version,
                    json.dumps(config_payload),
                    change_summary, changed_by,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def upsert_plan_link(
        self,
        tenant_id: str,
        plan_id: str,
        link_status: str = "active",
        plan_version: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        updated_by: str | None = None,
    ) -> None:
        """Create or update a tenant plan link (SPEC_04 §3.1.4)."""
        tid = self._require_tenant_id(tenant_id)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tenant_plan_links
                   (tenant_id, plan_id, plan_version, effective_from, effective_to,
                    link_status, updated_by, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, plan_id) DO UPDATE SET
                     plan_version = excluded.plan_version,
                     effective_from = excluded.effective_from,
                     effective_to = excluded.effective_to,
                     link_status = excluded.link_status,
                     updated_by = excluded.updated_by,
                     updated_at = excluded.updated_at""",
                (
                    tid, plan_id, plan_version,
                    effective_from.isoformat() if effective_from else None,
                    effective_to.isoformat() if effective_to else None,
                    link_status, updated_by, now,
                ),
            )

    def upsert_isolation_policy(
        self,
        tenant_id: str,
        partition_key: str | None = None,
        residency_constraints: str | None = None,
        encryption_profile_ref: str | None = None,
        cross_tenant_access_policy: str = "deny",
    ) -> None:
        """Create or update the isolation policy for a tenant (SPEC_04 §3.1.5)."""
        tid = self._require_tenant_id(tenant_id)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tenant_isolation_policies
                   (tenant_id, partition_key, residency_constraints, encryption_profile_ref,
                    cross_tenant_access_policy, policy_version, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)
                   ON CONFLICT(tenant_id) DO UPDATE SET
                     partition_key = excluded.partition_key,
                     residency_constraints = excluded.residency_constraints,
                     encryption_profile_ref = excluded.encryption_profile_ref,
                     cross_tenant_access_policy = excluded.cross_tenant_access_policy,
                     policy_version = policy_version + 1,
                     updated_at = excluded.updated_at""",
                (
                    tid, partition_key or tid,
                    residency_constraints, encryption_profile_ref,
                    cross_tenant_access_policy, now,
                ),
            )

    def list_tenants(self) -> list[Tenant]:
        """Return all tenants. (Admin/platform-level; no tenant_id filter needed here.)"""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tenants ORDER BY created_at").fetchall()
        return [_load_tenant(dict(r)) for r in rows]
