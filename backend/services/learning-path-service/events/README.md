# Learning Path Service Domain Events

This directory defines versioned event contracts emitted by `learning_path_service`.

## Events
- `learning_path_created`
- `learning_path_updated`
- `learning_path_assigned`
- `learning_path_completed`

## Notes
- Naming follows snake_case and past-tense semantics requested for this batch.
- Payload attributes align with learning path topology, assignment scope, completion rules, and auditability constraints defined in `/docs/specs/learning_path_spec.md`.
- Consumer lists align with LMS service boundaries and event-driven integration patterns from architecture specs.
