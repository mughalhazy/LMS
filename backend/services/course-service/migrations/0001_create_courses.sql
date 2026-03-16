CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NULL,
    created_by TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category_id TEXT NULL,
    language TEXT NOT NULL DEFAULT 'en-US',
    delivery_mode TEXT NOT NULL,
    duration_minutes INTEGER NULL,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    published_version INTEGER NULL,
    published_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_courses_tenant_id ON courses(tenant_id);
CREATE INDEX IF NOT EXISTS ix_courses_org_id ON courses(organization_id);
