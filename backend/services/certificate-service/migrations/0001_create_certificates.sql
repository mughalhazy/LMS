CREATE TABLE IF NOT EXISTS certificates (
    certificate_id TEXT PRIMARY KEY,
    verification_code TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    enrollment_id TEXT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NULL,
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_uri TEXT NULL,
    revoked_at TIMESTAMPTZ NULL,
    revocation_reason TEXT NULL,
    CONSTRAINT uq_certificates_user_course UNIQUE (tenant_id, user_id, course_id)
);

CREATE INDEX IF NOT EXISTS ix_certificates_tenant_id ON certificates(tenant_id);
