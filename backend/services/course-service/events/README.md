# Course Service Domain Events

This directory contains versioned domain-event contracts emitted by `course-service`.

## Events defined
- `course_created` → `lms.course.created.v1`
- `course_updated` → `lms.course.updated.v1`
- `course_published` → `lms.course.published.v1`

## Ownership boundary note
- `course_enrolled.event.json` is intentionally retained as a compatibility alias for legacy readers, but its canonical topic and producer now point to `enrollment-service` (`lms.enrollment.created.v1`).
- New integrations should consume enrollment lifecycle contracts from `backend/services/enrollment-service/events`.

## Notes
- Event names follow the task-specified snake_case naming.
- Topic names follow the broader LMS bus convention (`lms.<domain>.<action>.v<version>`).
- Payload fields are aligned to course service operations in `/docs/specs/course_service_spec.md`.
