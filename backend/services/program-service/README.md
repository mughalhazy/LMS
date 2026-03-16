# program-service

`program-service` introduces a program container above courses and owns:
- program lifecycle and metadata
- institution linkage
- program-to-course mapping
- status transitions and audit/event emission

## API
Versioned endpoints are exposed under `/api/v1/programs`.

## Boundaries
- Wraps and organizes course entities but does **not** own course lifecycle.
- Does not own lessons, enrollments, or progress.
- Storage is service-local (no shared database writes).

## Local run
```bash
uvicorn app.main:app --reload --port 8016
```
