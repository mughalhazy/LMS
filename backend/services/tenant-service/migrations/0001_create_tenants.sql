CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    tenant_name TEXT NOT NULL,
    tenant_code TEXT NOT NULL UNIQUE,
    primary_domain TEXT NOT NULL UNIQUE,
    admin_user TEXT NOT NULL,
    data_residency_region TEXT NOT NULL,
    subscription_plan TEXT NOT NULL,
    isolation_mode TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL DEFAULT 'provisioning',
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
