-- Event ingestion service dedicated tables (no shared domain DB writes)
CREATE TABLE IF NOT EXISTS event_records (
    record_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    family TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    trace_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    actor JSONB,
    entity JSONB,
    payload JSONB NOT NULL,
    normalized_payload JSONB NOT NULL,
    tags JSONB NOT NULL,
    storage_partition TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_records_tenant_ingested_at
    ON event_records (tenant_id, ingested_at DESC);

CREATE TABLE IF NOT EXISTS event_audit_log (
    audit_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    action TEXT NOT NULL,
    event_id TEXT NOT NULL,
    at TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_audit_log_tenant_at
    ON event_audit_log (tenant_id, at DESC);
