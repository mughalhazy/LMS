# SCORM Runtime Module

Implements tenant-scoped SCORM launch and runtime tracking aligned to:
- `docs/specs/scorm_runtime_spec.md`
- `docs/specs/content_service_spec.md`
- `docs/architecture/core_system_architecture.md`

## Features

- SCORM package launch from `imsmanifest.xml` + SCO identifier.
- Session management with per-session token validation.
- Runtime API adapter for SCORM 1.2 (`LMS*`) and SCORM 2004 methods.
- Learner runtime session persistence in `data/scorm-sessions.json`.
- Strict tenant scoping on every session query/update.

## Run

```bash
cd backend/services/scorm-service/modules/scorm_runtime
npm install
npm start
```

## API Endpoints

- `GET /health`
- `POST /tenants/:tenantId/scorm/launch`
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/runtime` (`x-scorm-session-token` header required)
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/commit` (`x-scorm-session-token` header required)
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/finish` (`x-scorm-session-token` header required)
- `GET /tenants/:tenantId/scorm/sessions/:sessionId`

## Launch request payload

```json
{
  "learnerId": "user-123",
  "courseId": "course-101",
  "registrationId": "enroll-888",
  "contentId": "content-555",
  "version": "2004",
  "launchMode": "normal",
  "scoIdentifier": "SCO_1",
  "manifestXml": "<manifest>...</manifest>"
}
```
