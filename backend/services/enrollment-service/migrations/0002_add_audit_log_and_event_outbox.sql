CREATE TABLE IF NOT EXISTS enrollment_audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    enrollment_id UUID NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enrollment_event_outbox (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    enrollment_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_enrollment_audit_tenant ON enrollment_audit_log(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_enrollment_outbox_tenant ON enrollment_event_outbox(tenant_id, created_at DESC);
