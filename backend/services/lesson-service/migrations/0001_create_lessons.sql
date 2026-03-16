CREATE TABLE IF NOT EXISTS lessons (
    lesson_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    module_id TEXT NULL,
    created_by TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NULL,
    lesson_type TEXT NOT NULL,
    learning_objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
    content_ref TEXT NULL,
    estimated_duration_minutes INTEGER NULL,
    availability_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    order_index INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    published_version INTEGER NULL,
    published_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_lessons_tenant_id ON lessons(tenant_id);
CREATE INDEX IF NOT EXISTS ix_lessons_course_id ON lessons(course_id);
