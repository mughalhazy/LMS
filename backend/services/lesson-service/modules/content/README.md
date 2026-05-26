# Lesson Content Module

This module implements lesson-content capabilities derived from:
- `docs/specs/features/lesson-service-spec.md`
- `docs/specs/features/content-service-spec.md`

## Implemented capabilities

1. Attach content to lesson (`attachContent`)
2. Manage lesson resources (`upsertResource`)
3. Content ordering inside lessons (`reorderContent`)
4. Content visibility rules (`listVisibleLessonContent` + `matchesVisibility`)

## API endpoints

> **Status: Proposed** — these endpoints are defined in the spec but live status has not been confirmed as of 2026-05-26. Verify against `app/main.py` before relying on these routes.

- `POST /lessons/{lessonId}/content`
- `PUT /lessons/{lessonId}/resources/{resourceId}`
- `PUT /lessons/{lessonId}/content/order`
- `GET /lessons/{lessonId}/content/visible`
