CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    lesson_id TEXT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    assessment_type TEXT NOT NULL,
    time_limit_minutes INTEGER NOT NULL,
    question_bank_id TEXT NULL,
    grading_rule_id TEXT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    published_at TIMESTAMPTZ NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_assessments_tenant_id ON assessments(tenant_id);
CREATE INDEX IF NOT EXISTS ix_assessments_course_id ON assessments(course_id);
