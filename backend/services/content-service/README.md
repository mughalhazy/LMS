# Content Service

Tenant-scoped content management service for LMS content-management boundaries.

> **Implementation language note:** This service has a mixed-language structure. The top-level service (`content_service/main.py`, API endpoints, tests) is **Python/FastAPI**. The `modules/metadata/` and `modules/storage/` subdirectories are **TypeScript** (`.ts` files). This is intentional — the metadata and storage modules were built as TypeScript to leverage type-safe CDN/storage client libraries. Both runtimes are independently testable. New modules should document their language choice explicitly.

## Implemented capabilities
- Content upload for `video`, `audio`, `document`, `scorm_package`, and `assessment_asset`.
- Content metadata management (title, description, tags, language, duration, licensing, accessibility).
- Content retrieval with tenant-scoped filtering and access control.
- Content versioning — immutable draft/rollback/publish lifecycle per `docs/specs/features/content-versioning-spec.md`.

Authentication: JWT required (`Authorization: Bearer <token>`).

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/content/uploads` | Upload content asset |
| PATCH | `/api/v1/content/{content_id}/metadata` | Update metadata |
| GET | `/api/v1/content/{content_id}` | Retrieve with access enforcement + secure delivery URL |
| GET | `/api/v1/content` | List with filters (content_type, tags, language) |
| POST | `/api/v1/content/{content_id}/versions` | Create new draft version |
| GET | `/api/v1/content/{content_id}/versions` | List all versions |
| GET | `/api/v1/content/{content_id}/versions/{n}` | Get specific version |
| POST | `/api/v1/content/{content_id}/versions/{n}/rollback` | Clone version n as new draft (preserves history) |
| POST | `/api/v1/content/{content_id}/versions/{n}/publish` | Transition draft → published; updates live pointer |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

Versioning routes added 2026-05-31 (B04-001). See `app/main.py` for authoritative declarations.

## Development checks
```bash
python -m compileall backend/services/content-service/content_service
PYTHONPATH=backend/services/content-service python -m unittest discover -s backend/services/content-service/tests
```
