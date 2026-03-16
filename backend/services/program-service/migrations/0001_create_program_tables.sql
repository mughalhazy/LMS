-- program-service isolated schema migration
CREATE TABLE programs (
  program_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  institution_id UUID NOT NULL,
  code TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  visibility TEXT NOT NULL,
  start_date DATE,
  end_date DATE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by UUID NOT NULL,
  updated_by UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  mapping_version INT NOT NULL DEFAULT 0,
  UNIQUE (tenant_id, code)
);

CREATE TABLE program_institution_links (
  program_id UUID PRIMARY KEY REFERENCES programs(program_id),
  institution_id UUID NOT NULL,
  link_status TEXT NOT NULL,
  linked_at TIMESTAMPTZ,
  unlinked_at TIMESTAMPTZ,
  link_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE program_course_maps (
  program_id UUID REFERENCES programs(program_id),
  course_id UUID NOT NULL,
  sequence_order INT NOT NULL,
  is_required BOOLEAN NOT NULL,
  minimum_completion_pct INT,
  availability_rule JSONB,
  mapping_status TEXT NOT NULL,
  mapped_at TIMESTAMPTZ,
  unmapped_at TIMESTAMPTZ,
  PRIMARY KEY (program_id, course_id)
);

CREATE TABLE program_status_history (
  id BIGSERIAL PRIMARY KEY,
  program_id UUID NOT NULL REFERENCES programs(program_id),
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  changed_by UUID NOT NULL,
  change_reason TEXT NOT NULL,
  changed_at TIMESTAMPTZ NOT NULL
);
