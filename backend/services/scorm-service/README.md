# SCORM Service

SCORM runtime service implementing:
- SCORM launch
- SCORM session handling
- completion tracking

Aligned to `docs/specs/scorm_runtime_spec.md`.

> Stage-3 structure note: the SCORM runtime implementation now lives under `modules/scorm_runtime`.

## Endpoints

- `GET /health`
- `POST /tenants/:tenantId/scorm/launch`
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/runtime`
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/commit`
- `POST /tenants/:tenantId/scorm/sessions/:sessionId/finish`
- `GET /tenants/:tenantId/scorm/sessions/:sessionId`
- `GET /tenants/:tenantId/scorm/completions?registrationId=...`

## Run

```bash
npm install
npm test
npm start
```
