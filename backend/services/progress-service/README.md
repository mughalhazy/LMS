# Progress Tracking Service

This service implements progress tracking for:
- lesson completion tracking
- course completion tracking
- learning path progress
- tenant-scoped learner progress isolation

## Event Contracts Implemented

- `LessonCompletionTracked`
- `CourseCompletionTracked`
- `LearningPathProgressUpdated`

The event payload fields align with `docs/specs/progress_tracking_spec.md`.

## Data Model Mapping

The service follows tenant-scoped learner progression using schema entities from `docs/data/core_lms_schema.md`:
- tenants
- users (learner)
- courses
- lessons
- enrollments
- certificates (as output linkage for completed courses)

## API Summary

See `src/api_contract.md` for endpoint details.

## Local Test

```bash
python -m unittest discover -s backend/services/progress-service/tests -p 'test_*.py'
```
