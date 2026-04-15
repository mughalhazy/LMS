# Lesson Content Module

This module implements lesson-content capabilities derived from:
- `docs/specs/lesson_service_spec.md`
- `docs/specs/content_service_spec.md`

## Implemented capabilities

1. Attach content to lesson (`attachContent`)
2. Manage lesson resources (`upsertResource`)
3. Content ordering inside lessons (`reorderContent`)
4. Content visibility rules (`listVisibleLessonContent` + `matchesVisibility`)

## Proposed API endpoints

- `POST /lessons/{lessonId}/content`
- `PUT /lessons/{lessonId}/resources/{resourceId}`
- `PUT /lessons/{lessonId}/content/order`
- `GET /lessons/{lessonId}/content/visible`
