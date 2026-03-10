event_type
fields
storage_destination

EventCollected
collection_id, event_id, event_type, source_system, tenant_id, actor_id, session_id, occurred_at, received_at, schema_version, payload, ingestion_channel
Raw event landing zone (append-only object storage partitioned by event_date/tenant_id) for replay and audit.

EventValidated
validation_id, event_id, event_type, tenant_id, schema_version, required_fields_present, pii_policy_passed, signature_verified, validation_status, validated_at, validator_version, normalized_payload
Validated event stream in analytics bronze table (Delta/Iceberg/Kafka topic) used for downstream transformation.

EventRejected
rejection_id, event_id, event_type, tenant_id, received_at, rejection_reason_code, rejection_reason_detail, failed_field, validator_version, original_payload, retry_eligible_flag
Quarantine store (dead-letter queue + rejected_events table) with retention policy for remediation and replay.
