CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NULL,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    role_set JSONB NOT NULL DEFAULT '[]'::jsonb,
    auth_provider TEXT NOT NULL,
    external_subject_id TEXT NULL,
    profile JSONB NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending_activation',
    profile_version INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ NULL,
    lifecycle_timeline JSONB NOT NULL DEFAULT '[]'::jsonb,
    identity_links JSONB NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email),
    CONSTRAINT uq_users_tenant_username UNIQUE (tenant_id, username)
);

CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id);
