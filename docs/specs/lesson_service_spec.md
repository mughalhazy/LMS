operation | input_fields | output
--- | --- | ---
create_lesson | tenant_id, course_id, module_id?, created_by, title, description?, lesson_type(video\|document\|quiz\|scorm\|live_session), learning_objectives[], content_ref?, estimated_duration_minutes?, availability_rules?, metadata? | lesson_id, course_id, module_id?, status(draft), order_index, version(1), created_at, updated_at
update_lesson | tenant_id, lesson_id, updated_by, title?, description?, lesson_type?, learning_objectives[]?, content_ref?, estimated_duration_minutes?, availability_rules?, metadata? | lesson_id, status, version, updated_fields[], updated_at
reorder_lessons | tenant_id, course_id, updated_by, ordered_lesson_ids[] | course_id, lesson_order[](lesson_id, order_index), reordered_at
publish_lesson | tenant_id, lesson_id, requested_by, publish_notes?, scheduled_publish_at?, visibility_rules?, prerequisite_rules? | lesson_id, status(published), published_version, published_at, effective_from
create_lesson_version | tenant_id, lesson_id, based_on_version, created_by, change_summary, cloned_content_refs[]?, metadata_overrides? | lesson_id, new_version, status(draft), version_id, created_at
archive_lesson | tenant_id, lesson_id, archived_by, reason_code, archive_notes? | lesson_id, status(archived), archived_at
