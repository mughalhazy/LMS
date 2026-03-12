# Core REST APIs for LMS

endpoint | method | description
--- | --- | ---
`/users` | `POST` | Create a new LMS user profile (learner, instructor, or admin).
`/users` | `GET` | List users with optional filters (role, status, department) and pagination.
`/users/{userId}` | `GET` | Retrieve a specific user’s full profile and account metadata.
`/users/{userId}` | `PATCH` | Update user attributes such as name, role, status, or department.
`/users/{userId}` | `DELETE` | Deactivate or remove a user account.

`/courses` | `POST` | Create a new course with catalog metadata and publish settings.
`/courses` | `GET` | List available courses with filtering by category, status, or owner.
`/courses/{courseId}` | `GET` | Retrieve detailed course information and configuration.
`/courses/{courseId}` | `PATCH` | Update course metadata, schedule, or publication status.
`/courses/{courseId}` | `DELETE` | Archive or delete a course.

`/lessons` | `POST` | Create a lesson and attach it to a course/module structure.
`/lessons` | `GET` | List lessons with filters (course, type, published state).
`/lessons/{lessonId}` | `GET` | Retrieve lesson details including content references.
`/lessons/{lessonId}` | `PATCH` | Update lesson content metadata, sequencing, or visibility.
`/lessons/{lessonId}` | `DELETE` | Remove a lesson from active catalog delivery.

`/enrollments` | `POST` | Enroll a user into a course or learning path.
`/enrollments` | `GET` | List enrollments by user, course, status, or date range.
`/enrollments/{enrollmentId}` | `GET` | Retrieve enrollment details including current progress state.
`/enrollments/{enrollmentId}` | `PATCH` | Update enrollment status (approved, waitlisted, completed, withdrawn).
`/enrollments/{enrollmentId}` | `DELETE` | Cancel or remove an enrollment record.

`/assessments` | `POST` | Create an assessment (quiz/exam) with scoring policy.
`/assessments` | `GET` | List assessments with filters for course, type, and publish state.
`/assessments/{assessmentId}` | `GET` | Retrieve assessment structure, rules, and metadata.
`/assessments/{assessmentId}` | `PATCH` | Update assessment questions, timing, or grading criteria.
`/assessments/{assessmentId}` | `DELETE` | Retire or remove an assessment.

`/certificates` | `POST` | Issue a certificate for a user after completion criteria are met.
`/certificates` | `GET` | List certificates by user, course, issuance date, or expiration status.
`/certificates/{certificateId}` | `GET` | Retrieve certificate details and verification metadata.
`/certificates/{certificateId}` | `PATCH` | Update certificate validity, metadata, or revocation reason.
`/certificates/{certificateId}` | `DELETE` | Revoke or delete a certificate record.
