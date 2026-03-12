CREATE TABLE departments (
    department_id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    parent_department_id UUID NULL REFERENCES departments (department_id),
    department_head_user_id TEXT NULL,
    cost_center TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (organization_id, name),
    UNIQUE (organization_id, code)
);

CREATE TABLE department_memberships (
    membership_id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    department_id UUID NOT NULL REFERENCES departments (department_id),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (department_id, user_id, role)
);
