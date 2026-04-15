CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    parent_organization_id TEXT NULL REFERENCES organizations(organization_id),
    primary_admin_user_id TEXT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    locale TEXT NOT NULL DEFAULT 'en-US',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_org_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_org_tenant_id ON organizations(tenant_id);
