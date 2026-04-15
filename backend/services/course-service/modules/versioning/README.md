# Course Versioning Module

Implements content versioning for course artifacts aligned with:
- `docs/specs/content_versioning_spec.md`
- `docs/specs/course_service_spec.md`

## Capabilities

- Version creation with immutable snapshots and payload diffing.
- Version history with pagination and draft/published pointers.
- Rollback by creating a new draft cloned from a target version.
- Publish workflow to move draft to published state.
- Automatic superseding of previously active drafts.

## REST Endpoints

- `POST /courses/:courseId/versions`
- `GET /courses/:courseId/versions`
- `POST /courses/:courseId/versions/:versionNumber/rollback`
- `POST /courses/:courseId/versions/:versionNumber/publish`
