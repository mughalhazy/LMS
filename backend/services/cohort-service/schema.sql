-- cohort-service bounded-context schema (owned by cohort-service only)

CREATE TABLE cohorts (
  cohort_id UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  code TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('formal_cohort', 'academy_batch', 'tutor_group')),
  status TEXT NOT NULL CHECK (status IN ('draft', 'scheduled', 'active', 'completed', 'archived', 'cancelled')),
  program_id TEXT NULL,
  schedule_starts_at TIMESTAMPTZ NULL,
  schedule_ends_at TIMESTAMPTZ NULL,
  schedule_timezone TEXT NOT NULL DEFAULT 'UTC',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  UNIQUE (tenant_id, code)
);

CREATE TABLE cohort_memberships (
  membership_id UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  cohort_id UUID NOT NULL REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  joined_at TIMESTAMPTZ NOT NULL,
  added_by TEXT NOT NULL,
  UNIQUE (tenant_id, cohort_id, user_id)
);

CREATE INDEX idx_cohorts_tenant_kind_status ON cohorts(tenant_id, kind, status);
CREATE INDEX idx_cohort_memberships_tenant_cohort ON cohort_memberships(tenant_id, cohort_id);
