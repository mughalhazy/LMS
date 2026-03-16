CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    department_head_user_id TEXT NULL,
    cost_center TEXT NULL,
    parent_department_id TEXT NULL REFERENCES departments(department_id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_departments_org FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT uq_dept_org_code UNIQUE (organization_id, code)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    department_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    team_lead_user_id TEXT NULL,
    capacity INTEGER NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_teams_department FOREIGN KEY (department_id) REFERENCES departments(department_id),
    CONSTRAINT uq_team_dept_code UNIQUE (department_id, code)
);

CREATE INDEX IF NOT EXISTS ix_departments_tenant_id ON departments(tenant_id);
CREATE INDEX IF NOT EXISTS ix_teams_tenant_id ON teams(tenant_id);
