"""SQLite-backed certificate store — persistent implementation of CertificateStore Protocol.

Tables:
  certificates            — Certificate (tenant-scoped; verification_code UNIQUE)
  certificate_templates   — CertificateTemplate (tenant-scoped; upsert with version increment)
  badge_extension_profiles — BadgeExtensionProfile (keyed by certificate_id — no tenant_id in model)

Architecture anchors:
  ARCH_04 — certificate-service-specific DB file; no cross-service writes.
  ARCH_07 — tenant_id NOT NULL on tenant-scoped tables; tenant-first query pattern.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.services.shared.db import BaseRepository, resolve_db_path
from .models import (
    BadgeExtensionProfile,
    Certificate,
    CertificateStatus,
    CertificateTemplate,
    CompletionRef,
)
from .store import CertificateStore


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SQLiteCertificateStore(BaseRepository):
    """Persistent CertificateStore backed by SQLite.

    Implements CertificateStore Protocol — drop-in for InMemoryCertificateStore.
    """

    _SERVICE_NAME = "certificate-service"

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path or resolve_db_path(self._SERVICE_NAME))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS certificates (
                    certificate_id      TEXT NOT NULL,
                    tenant_id           TEXT NOT NULL,
                    verification_code   TEXT NOT NULL UNIQUE,
                    user_id             TEXT NOT NULL,
                    course_id           TEXT NOT NULL,
                    enrollment_id       TEXT,
                    template_id         TEXT NOT NULL,
                    status              TEXT NOT NULL DEFAULT 'active',
                    issued_at           TEXT NOT NULL,
                    expires_at          TEXT,
                    artifact_uri        TEXT,
                    metadata            TEXT NOT NULL DEFAULT '{}',
                    completion_ref      TEXT,
                    revoked_at          TEXT,
                    revocation_reason   TEXT,
                    PRIMARY KEY (tenant_id, certificate_id)
                );
                CREATE INDEX IF NOT EXISTS idx_certs_user_course
                    ON certificates (tenant_id, user_id, course_id, status);

                CREATE TABLE IF NOT EXISTS certificate_templates (
                    template_id     TEXT NOT NULL,
                    tenant_id       TEXT NOT NULL,
                    name            TEXT NOT NULL,
                    version         INTEGER NOT NULL DEFAULT 1,
                    body            TEXT NOT NULL,
                    metadata        TEXT NOT NULL DEFAULT '{}',
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, template_id)
                );

                CREATE TABLE IF NOT EXISTS badge_extension_profiles (
                    certificate_id  TEXT PRIMARY KEY NOT NULL,
                    provider        TEXT NOT NULL,
                    badge_class_id  TEXT NOT NULL,
                    evidence_url    TEXT,
                    metadata        TEXT NOT NULL DEFAULT '{}'
                );
            """)

    # ---------------------------------------------------------------- #
    # CertificateStore Protocol — certificates                         #
    # ---------------------------------------------------------------- #

    def create_certificate(self, certificate: Certificate) -> None:
        tid = self._require_tenant_id(certificate.tenant_id)
        completion_ref_json = None
        if certificate.completion_ref:
            cr = certificate.completion_ref
            completion_ref_json = json.dumps({
                "source_event": cr.source_event,
                "source_event_id": cr.source_event_id,
                "completed_at": _iso(cr.completed_at),
            })
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO certificates
                   (certificate_id, tenant_id, verification_code, user_id, course_id,
                    enrollment_id, template_id, status, issued_at, expires_at,
                    artifact_uri, metadata, completion_ref, revoked_at, revocation_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    certificate.certificate_id, tid, certificate.verification_code,
                    certificate.user_id, certificate.course_id, certificate.enrollment_id,
                    certificate.template_id, certificate.status.value,
                    _iso(certificate.issued_at), _iso(certificate.expires_at),
                    certificate.artifact_uri, json.dumps(certificate.metadata),
                    completion_ref_json,
                    _iso(certificate.revoked_at), certificate.revocation_reason,
                ),
            )

    def get_certificate(self, *, tenant_id: str, certificate_id: str) -> Certificate | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "certificates", tid, "AND certificate_id = ?", (certificate_id,)
            )
        return _row_to_certificate(dict(row)) if row else None

    def find_by_verification_code(self, verification_code: str) -> Certificate | None:
        # verification_code is globally unique — no tenant scoping needed
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM certificates WHERE verification_code = ? LIMIT 1",
                (verification_code,),
            ).fetchone()
        return _row_to_certificate(dict(row)) if row else None

    def list_certificates(self, *, tenant_id: str) -> list[Certificate]:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            rows = self._fetch_all(conn, "certificates", tid, order_by="issued_at ASC")
        return [_row_to_certificate(dict(r)) for r in rows]

    def has_active_certificate(self, *, tenant_id: str, user_id: str, course_id: str) -> bool:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = conn.execute(
                """SELECT 1 FROM certificates
                   WHERE tenant_id = ? AND user_id = ? AND course_id = ? AND status = 'active'
                   LIMIT 1""",
                (tid, user_id, course_id),
            ).fetchone()
        return row is not None

    # ---------------------------------------------------------------- #
    # CertificateStore Protocol — templates                            #
    # ---------------------------------------------------------------- #

    def upsert_template(self, template: CertificateTemplate) -> CertificateTemplate:
        tid = self._require_tenant_id(template.tenant_id)
        with self._connect() as conn:
            existing = self._fetch_one(
                conn, "certificate_templates", tid,
                "AND template_id = ?", (template.template_id,)
            )
            if existing:
                template.version = existing["version"] + 1
            conn.execute(
                """INSERT INTO certificate_templates
                   (template_id, tenant_id, name, version, body, metadata, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant_id, template_id) DO UPDATE SET
                       name = excluded.name,
                       version = excluded.version,
                       body = excluded.body,
                       metadata = excluded.metadata,
                       updated_at = excluded.updated_at""",
                (
                    template.template_id, tid, template.name, template.version,
                    template.body, json.dumps(template.metadata),
                    _iso(template.created_at), _iso(template.updated_at),
                ),
            )
        return template

    def get_template(self, *, tenant_id: str, template_id: str) -> CertificateTemplate | None:
        tid = self._require_tenant_id(tenant_id)
        with self._connect() as conn:
            row = self._fetch_one(
                conn, "certificate_templates", tid, "AND template_id = ?", (template_id,)
            )
        return _row_to_template(dict(row)) if row else None

    # ---------------------------------------------------------------- #
    # CertificateStore Protocol — badge extensions                     #
    # ---------------------------------------------------------------- #

    def attach_badge_extension(self, extension: BadgeExtensionProfile) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO badge_extension_profiles
                   (certificate_id, provider, badge_class_id, evidence_url, metadata)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(certificate_id) DO UPDATE SET
                       provider = excluded.provider,
                       badge_class_id = excluded.badge_class_id,
                       evidence_url = excluded.evidence_url,
                       metadata = excluded.metadata""",
                (
                    extension.certificate_id, extension.provider, extension.badge_class_id,
                    extension.evidence_url, json.dumps(extension.metadata),
                ),
            )


# ---------------------------------------------------------------- #
# Deserialisation helpers                                           #
# ---------------------------------------------------------------- #

def _row_to_certificate(r: dict) -> Certificate:
    completion_ref = None
    if r.get("completion_ref"):
        cr = json.loads(r["completion_ref"])
        completion_ref = CompletionRef(
            source_event=cr["source_event"],
            source_event_id=cr["source_event_id"],
            completed_at=datetime.fromisoformat(cr["completed_at"]),
        )
    return Certificate(
        certificate_id=r["certificate_id"],
        verification_code=r["verification_code"],
        tenant_id=r["tenant_id"],
        user_id=r["user_id"],
        course_id=r["course_id"],
        enrollment_id=r.get("enrollment_id"),
        template_id=r["template_id"],
        status=CertificateStatus(r["status"]),
        issued_at=datetime.fromisoformat(r["issued_at"]),
        expires_at=_dt(r.get("expires_at")),
        artifact_uri=r.get("artifact_uri"),
        metadata=json.loads(r["metadata"]),
        completion_ref=completion_ref,
        revoked_at=_dt(r.get("revoked_at")),
        revocation_reason=r.get("revocation_reason"),
    )


def _row_to_template(r: dict) -> CertificateTemplate:
    return CertificateTemplate(
        template_id=r["template_id"],
        tenant_id=r["tenant_id"],
        name=r["name"],
        version=r["version"],
        body=r["body"],
        metadata=json.loads(r["metadata"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )
