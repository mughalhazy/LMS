CREATE TABLE groups (
  group_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  organization_id UUID NOT NULL,
  name VARCHAR(200) NOT NULL,
  code VARCHAR(100) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'active', 'inactive', 'archived')),
  created_by UUID NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE (tenant_id, organization_id, lower(name)),
  UNIQUE (tenant_id, organization_id, lower(code))
);

CREATE TABLE group_memberships (
  membership_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  group_id UUID NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  role VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'removed')),
  added_by UUID NOT NULL,
  added_at TIMESTAMPTZ NOT NULL,
  removed_at TIMESTAMPTZ,
  UNIQUE (tenant_id, group_id, user_id)
);

CREATE TABLE group_learning_assignments (
  assignment_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  group_id UUID NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
  assignment_type VARCHAR(30) NOT NULL CHECK (assignment_type IN ('course', 'learning_path')),
  learning_object_id UUID NOT NULL,
  target VARCHAR(40) NOT NULL CHECK (target IN ('current_members', 'current_and_future_members')),
  assigned_by UUID NOT NULL,
  assigned_at TIMESTAMPTZ NOT NULL,
  due_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (tenant_id, group_id, assignment_type, learning_object_id)
);
