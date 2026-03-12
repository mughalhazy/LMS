version_operation
inputs
result

version creation
content_id, tenant_id, source_version (optional), change_summary, editor_id, content_payload, metadata_updates, validation_policy
Creates a new immutable draft version with incremented version_number, stores payload snapshot and diff, records audit metadata (created_by/created_at), and sets status to draft.

version rollback
content_id, tenant_id, target_version_number, rollback_reason, requested_by
Creates a new draft version cloned from target_version_number (without deleting newer history), links rollback_origin_version, logs rollback event in audit trail, and marks previous active draft as superseded.

version publishing
content_id, tenant_id, version_number, publisher_id, release_notes, publish_scope (course/module/global), scheduled_at (optional)
Transitions the specified version from draft/review to published after validation checks, updates live content pointer to this version, timestamps published_at, and emits publication event for downstream caches/search/indexing.
