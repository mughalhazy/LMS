# Content Service

Tenant-scoped content management service for LMS content-management boundaries.

> **Implementation language note:** This service has a mixed-language structure. The top-level service (`content_service/main.py`, API endpoints, tests) is **Python/FastAPI**. The `modules/metadata/` and `modules/storage/` subdirectories are **TypeScript** (`.ts` files). This is intentional — the metadata and storage modules were built as TypeScript to leverage type-safe CDN/storage client libraries. Both runtimes are independently testable. New modules should document their language choice explicitly.

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
