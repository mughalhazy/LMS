CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    learner_id TEXT NOT NULL,
    learning_object_id TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    mode TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unenrolled_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_enrollments_learner_object UNIQUE (tenant_id, learner_id, learning_object_id)
);

CREATE INDEX IF NOT EXISTS ix_enrollments_tenant_id ON enrollments(tenant_id);
