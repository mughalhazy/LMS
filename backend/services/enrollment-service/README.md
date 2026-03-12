# Enrollment Service

In-memory enrollment lifecycle service for LMS learning objects (courses or learning paths).

## Implemented capabilities

- Enroll learner (`EnrollmentService.enroll_learner`)
- Unenroll learner (`EnrollmentService.unenroll_learner`)
- Enrollment status lookup (`EnrollmentService.get_enrollment_status`)
- Enrollment rule configuration and enforcement (`EnrollmentService.set_enrollment_rules`)

## Rules supported

- self-enrollment enable/disable
- manager approval requirement for self-enrollment
- enrollment capacity with optional waitlist
- prerequisite enforcement

## Run tests

```bash
cd backend/services/enrollment-service
PYTHONPATH=. pytest -q
```
