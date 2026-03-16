-- institution-service owns only institution governance records.
-- No writes are made into runtime LMS domain tables (courses, lessons, enrollments, progress, certificates).

CREATE TABLE institutions (
  institution_id VARCHAR(32) PRIMARY KEY,
  tenant_id VARCHAR(32) NOT NULL,
  institution_type VARCHAR(64) NOT NULL,
  legal_name VARCHAR(255) NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  status VARCHAR(32) NOT NULL,
  registration_country VARCHAR(2),
  default_locale VARCHAR(16) NOT NULL,
  timezone VARCHAR(64) NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE institution_types (
  type_code VARCHAR(64) PRIMARY KEY,
  type_name VARCHAR(255) NOT NULL,
  is_system_type BOOLEAN NOT NULL DEFAULT FALSE,
  governance_profile JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE institution_hierarchy_edges (
  edge_id VARCHAR(32) PRIMARY KEY,
  parent_institution_id VARCHAR(32) NOT NULL REFERENCES institutions(institution_id),
  child_institution_id VARCHAR(32) NOT NULL REFERENCES institutions(institution_id),
  relationship_type VARCHAR(64) NOT NULL,
  status VARCHAR(16) NOT NULL,
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ
);

CREATE TABLE institution_tenant_links (
  link_id VARCHAR(32) PRIMARY KEY,
  institution_id VARCHAR(32) NOT NULL REFERENCES institutions(institution_id),
  tenant_id VARCHAR(32) NOT NULL,
  link_scope VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL,
  linked_at TIMESTAMPTZ NOT NULL
);
