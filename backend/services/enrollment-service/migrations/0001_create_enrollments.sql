CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    learner_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    assignment_source TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    cohort_id TEXT NULL,
    session_id TEXT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_enrollment_status CHECK (status IN ('assigned', 'active', 'completed', 'withdrawn', 'cancelled'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_enrollment
ON enrollments (tenant_id, learner_id, course_id)
WHERE status IN ('assigned', 'active');

CREATE INDEX IF NOT EXISTS ix_enrollments_tenant_learner ON enrollments(tenant_id, learner_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_tenant_course ON enrollments(tenant_id, course_id);
