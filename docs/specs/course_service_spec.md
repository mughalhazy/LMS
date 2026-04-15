> **DEPRECATED** — Superseded by: `docs/specs/SPEC_09_course_service.md`
> Reason: SPEC_ prefixed doc is the canonical spec. This legacy spec is retained for historical reference only.
> Last reviewed: 2026-04-04

operation | input_fields | output
--- | --- | ---
create_course | tenant_id, created_by, title, description, category_id, language, delivery_mode, duration_minutes, tags[], objectives[], metadata | course_id, status(draft), version(1), created_at, updated_at
update_course | tenant_id, course_id, updated_by, title?, description?, category_id?, language?, delivery_mode?, duration_minutes?, tags[]?, objectives[]?, metadata? | course_id, status, version, updated_fields[], updated_at
publish_course | tenant_id, course_id, requested_by, publish_notes?, scheduled_publish_at?, audience_rules? | course_id, status(published), published_version, published_at, effective_from
create_course_version | tenant_id, course_id, based_on_version, created_by, change_summary, cloned_content_refs[]?, metadata_overrides? | course_id, new_version, status(draft), version_id, created_at
