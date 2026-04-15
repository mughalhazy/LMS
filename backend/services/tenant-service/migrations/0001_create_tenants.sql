CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_code CHAR(2) NOT NULL,
    segment_type TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    addon_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    isolation_mode TEXT NOT NULL CHECK (isolation_mode IN ('schema_per_tenant', 'database_per_tenant')),
    lifecycle_state TEXT NOT NULL DEFAULT 'provisioning',
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_lifecycle_events (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    state TEXT NOT NULL,
    reason TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
