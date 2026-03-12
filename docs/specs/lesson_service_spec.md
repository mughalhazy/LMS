lesson_operation | input_fields | output
--- | --- | ---
lesson creation | `course_id`, `title`, `description`, `lesson_type`, `learning_objectives`, `content_ref`, `created_by` | `lesson_id`, `course_id`, `title`, `status` (`draft`), `order_index`, `created_at`
lesson ordering | `course_id`, `ordered_lesson_ids` (array in desired sequence), `updated_by` | `course_id`, `lesson_order` (lesson_id + order_index), `reordered_at`
lesson publishing | `lesson_id`, `publish_at` (optional), `published_by`, `visibility_rules` (optional) | `lesson_id`, `status` (`published`), `published_at`, `version`
