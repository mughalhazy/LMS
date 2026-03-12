# Content Service

Tenant-scoped content management service for LMS content-management boundaries.

## Implemented capabilities
- Content upload for `video`, `audio`, `document`, `scorm_package`, and `assessment_asset`.
- Content metadata management (title, description, tags, language, duration, licensing, accessibility).
- Content retrieval with tenant-scoped filtering.
- Content access control with visibility + allowed roles + allowed users.
- Tenant data isolation (`tenant_id` enforced in every repository query).

## API endpoints (gateway contract)
- `POST /content/uploads`
- `PATCH /content/{content_id}/metadata`
- `GET /content/{content_id}`
- `GET /content`

See `content_service/main.py` for endpoint contract declarations.

## Development checks
```bash
python -m compileall backend/services/content-service/content_service
PYTHONPATH=backend/services/content-service python -m unittest discover -s backend/services/content-service/tests
```
