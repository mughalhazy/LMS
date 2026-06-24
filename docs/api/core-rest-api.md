# Core REST APIs for LMS

**Type:** API Reference | **Last reviewed:** 2026-05-31
**CAT-024 fix:** Paths updated to reflect actual `/api/v1/` versioned prefix used by all services.

Core CRUD endpoints for the primary LMS entities. See `docs/api/api-gateway-design.md` for gateway
configuration and `docs/api/api-spec-validation-report.md` for known gaps.

---

| endpoint | method | description |
--- | --- | ---
`/api/v1/users` | `POST` | Create a new LMS user profile (learner, instructor, or admin).
`/api/v1/users` | `GET` | List users with optional filters (role, status, department) and pagination.
`/api/v1/users/{userId}` | `GET` | Retrieve a specific user's full profile and account metadata.
`/api/v1/users/{userId}` | `PATCH` | Update user attributes such as name, role, status, or department.
`/api/v1/users/{userId}` | `DELETE` | Deactivate or remove a user account (soft-delete).

`/api/v1/courses` | `POST` | Create a new course with catalog metadata and publish settings.
`/api/v1/courses` | `GET` | List available courses with filtering by category, status, or owner.
`/api/v1/courses/{courseId}` | `GET` | Retrieve detailed course information and configuration. Returns `ETag` header with version.
`/api/v1/courses/{courseId}` | `PATCH` | Update course metadata. Accepts `If-Match` header for OCC.
`/api/v1/courses/{courseId}/publish` | `POST` | Publish course (validates readiness rules).
`/api/v1/courses/{courseId}/archive` | `POST` | Archive a course.
`/api/v1/courses/{courseId}/program-links` | `PUT` | Replace program linkage set.
`/api/v1/courses/{courseId}/session-links` | `PUT` | Replace session linkage set.

`/api/v1/lessons` | `POST` | Create a lesson (flat path).
`/api/v1/courses/{courseId}/lessons` | `POST` | Create a lesson nested under course (canonical).
`/api/v1/lessons/{lessonId}` | `GET` | Retrieve lesson details including content references.
`/api/v1/lessons/{lessonId}` | `PATCH` | Update lesson content metadata, sequencing, or visibility.
`/api/v1/lessons/{lessonId}` | `DELETE` | Remove a lesson (soft-delete / archive).
`/api/v1/lessons/{lessonId}:publish` | `POST` | Publish lesson.
`/api/v1/courses/{courseId}/lessons:reorder` | `PUT` | Reorder lessons within a course.

`/api/v1/enrollments` | `POST` | Enroll a user into a course or learning path.
`/api/v1/enrollments` | `GET` | List enrollments by user, course, status, or date range. Returns pagination envelope.
`/api/v1/enrollments/{enrollmentId}` | `GET` | Retrieve enrollment details including current progress state.
`/api/v1/enrollments/{enrollmentId}/transitions` | `POST` | Transition enrollment status.
`/api/v1/enrollments/{enrollmentId}/links` | `PATCH` | Update cohort/session linkage.
`/api/v1/enrollments/bulk-assign` | `POST` | Bulk-assign learners to a course (202 response).

`/api/v1/assessments` | `POST` | Create an assessment (quiz/exam) with scoring policy.
`/api/v1/assessments` | `GET` | List assessments with filters for course, type, and publish state.
`/api/v1/assessments/{assessmentId}` | `GET` | Retrieve assessment structure, rules, and metadata.
`/api/v1/assessments/{assessmentId}` | `PATCH` | Update assessment questions, timing, or grading criteria.
`/api/v1/assessments/{assessmentId}/attempts` | `POST` | Start an attempt.
`/api/v1/attempts/{attemptId}/submissions` | `POST` | Submit attempt answers.
`/api/v1/attempts/{attemptId}/grade` | `POST` | Attach grade result.

`/api/v1/cohorts` | `POST` | Create cohort/batch/tutor group.
`/api/v1/cohorts` | `GET` | List cohorts for tenant.
`/api/v1/cohorts/{cohortId}` | `GET` | Retrieve cohort with memberships.
`/api/v1/cohorts/{cohortId}` | `PATCH` | Update mutable cohort properties.
`/api/v1/cohorts/bulk` | `POST` | Bulk create cohorts (207 multi-status).
`/api/v1/cohorts/bulk/status` | `PATCH` | Bulk update cohort status (207 multi-status).

`/api/v1/rbac/roles` | `POST` | Create tenant role definition.
`/api/v1/rbac/assignments` | `POST` | Create subject-role assignment.
`/api/v1/rbac/authorize` | `POST` | Evaluate single authorization decision.
`/api/v1/rbac/authorize/batch` | `POST` | Evaluate multiple authorization decisions.

`/api/v2/auth/sessions/login` | `POST` | Authenticate and receive tokens. (Auth service is on v2.)
`/api/v2/auth/tokens/refresh` | `POST` | Rotate refresh token.
`/api/v2/auth/sessions/validate` | `POST` | Validate access token / introspect session.

---

## Common headers

All API endpoints require:
- `X-Tenant-Id: <tenant_id>` — tenant isolation key
- `Authorization: Bearer <access_token>` — for authenticated endpoints
- `X-API-Version: v1` — version the client was built against (returned in response per versioning strategy)

## Pagination envelope

List endpoints return:
```json
{ "items": [...], "page": 1, "page_size": 50, "total": 123 }
```

## Error envelope

```json
{ "detail": "error_code_or_message" }
```

---

## See also
- `docs/specs/tenant-service-spec.md` — tenant service spec
- `docs/specs/course-service-spec.md` — course service spec
- `docs/api/auth-service-api.md` — auth service API (v2)
- `docs/architecture/microservice-boundary-map.md` — microservice boundary map
- `docs/architecture/api-versioning-strategy.md` — versioning rules
