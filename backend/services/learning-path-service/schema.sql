-- Learning Path Service schema (tenant-scoped, shared database model)

CREATE TABLE IF NOT EXISTS learning_paths (
  path_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'published', 'archived')),
  owner_id UUID NOT NULL,
  audience JSONB,
  completion_mode VARCHAR(40) NOT NULL DEFAULT 'all_required_complete'
    CHECK (completion_mode IN ('all_required_complete', 'required_plus_n_electives', 'milestone_based', 'score_threshold')),
  required_elective_count INTEGER,
  strict_due_date BOOLEAN NOT NULL DEFAULT FALSE,
  recertification_interval_days INTEGER,
  version INTEGER NOT NULL DEFAULT 1,
  published_at TIMESTAMPTZ,
  published_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, path_id)
);

CREATE INDEX IF NOT EXISTS idx_learning_paths_tenant_status ON learning_paths (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_learning_paths_tenant_owner ON learning_paths (tenant_id, owner_id);

CREATE TABLE IF NOT EXISTS learning_path_nodes (
  node_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  path_id UUID NOT NULL,
  node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('course', 'assessment', 'milestone')),
  ref_id UUID NOT NULL,
  sequence_index INTEGER NOT NULL,
  is_required BOOLEAN NOT NULL,
  min_score NUMERIC(5,2),
  estimated_duration_mins INTEGER,
  elective_group_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_learning_path_nodes_path
    FOREIGN KEY (path_id) REFERENCES learning_paths (path_id) ON DELETE CASCADE,
  UNIQUE (tenant_id, path_id, sequence_index),
  UNIQUE (tenant_id, path_id, node_id)
);

CREATE INDEX IF NOT EXISTS idx_learning_path_nodes_tenant_path ON learning_path_nodes (tenant_id, path_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_nodes_ref ON learning_path_nodes (tenant_id, ref_id);

CREATE TABLE IF NOT EXISTS learning_path_edges (
  edge_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  path_id UUID NOT NULL,
  from_node_id UUID NOT NULL,
  to_node_id UUID NOT NULL,
  relation VARCHAR(20) NOT NULL CHECK (relation IN ('prerequisite', 'next', 'branch', 'branch_merge')),
  condition JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_learning_path_edges_path
    FOREIGN KEY (path_id) REFERENCES learning_paths (path_id) ON DELETE CASCADE,
  CONSTRAINT fk_learning_path_edges_from_node
    FOREIGN KEY (from_node_id) REFERENCES learning_path_nodes (node_id) ON DELETE CASCADE,
  CONSTRAINT fk_learning_path_edges_to_node
    FOREIGN KEY (to_node_id) REFERENCES learning_path_nodes (node_id) ON DELETE CASCADE,
  CHECK (from_node_id <> to_node_id),
  UNIQUE (tenant_id, path_id, from_node_id, to_node_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_learning_path_edges_tenant_path ON learning_path_edges (tenant_id, path_id);

CREATE TABLE IF NOT EXISTS learning_path_elective_groups (
  group_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  path_id UUID NOT NULL,
  name VARCHAR(200) NOT NULL,
  min_select INTEGER NOT NULL DEFAULT 0,
  max_select INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_learning_path_elective_groups_path
    FOREIGN KEY (path_id) REFERENCES learning_paths (path_id) ON DELETE CASCADE,
  CHECK (min_select >= 0),
  CHECK (max_select IS NULL OR max_select >= min_select),
  UNIQUE (tenant_id, path_id, group_id)
);

CREATE TABLE IF NOT EXISTS learning_path_assignments (
  scope_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  path_id UUID NOT NULL,
  assignment_type VARCHAR(20) NOT NULL CHECK (assignment_type IN ('role', 'department', 'location', 'manual')),
  target_ref VARCHAR(255) NOT NULL,
  effective_from TIMESTAMPTZ,
  effective_to TIMESTAMPTZ,
  created_by UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_learning_path_assignments_path
    FOREIGN KEY (path_id) REFERENCES learning_paths (path_id) ON DELETE CASCADE,
  CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from),
  UNIQUE (tenant_id, path_id, assignment_type, target_ref)
);

CREATE INDEX IF NOT EXISTS idx_learning_path_assignments_tenant_target
  ON learning_path_assignments (tenant_id, assignment_type, target_ref);

CREATE TABLE IF NOT EXISTS learning_path_audit_log (
  audit_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  path_id UUID NOT NULL,
  path_version INTEGER NOT NULL,
  actor_id UUID NOT NULL,
  action VARCHAR(40) NOT NULL,
  change_reason TEXT,
  payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_learning_path_audit_log_path
    FOREIGN KEY (path_id) REFERENCES learning_paths (path_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learning_path_audit_log_tenant_path
  ON learning_path_audit_log (tenant_id, path_id, path_version, created_at DESC);
