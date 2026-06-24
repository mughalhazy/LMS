# HRIS Sync Service

Implements LMS HRIS synchronization capabilities described in `docs/integrations/hris-sync-spec.md`.

## API Endpoints

All routes require `X-Tenant-Id` header.

### Sync operations
- `POST /api/v1/hris/sync/roles` — sync role records from HRIS
- `POST /api/v1/hris/sync/departments` — sync department/org hierarchy from HRIS
- `POST /api/v1/hris/sync/employees` — sync employee records from HRIS
- `POST /api/v1/hris/sync/full` — run all three in dependency order (roles → departments → employees)

### Sync sessions
- `POST /api/v1/hris/sessions` — start sync session
- `GET /api/v1/hris/sessions` — list sync sessions
- `GET /api/v1/hris/sessions/{session_id}` — get session
- `POST /api/v1/hris/sessions/{session_id}/complete` — complete session

### Job management
- `PUT /api/v1/hris/jobs/{job_name}` — upsert scheduled sync job
- `GET /api/v1/hris/jobs` — list sync jobs
- `POST /api/v1/hris/jobs/run-due` — run all due sync jobs

### Data reads
- `GET /api/v1/hris/users` — list synced users
- `GET /api/v1/hris/departments` — list synced departments
- `GET /api/v1/hris/roles` — list synced roles

### Audit
- `GET /api/v1/hris/audit?operation={op}` — sync audit log (filter: `role_mapping` | `department_mapping` | `employee_sync`)

### Utility
- `GET /health`
- `GET /metrics`

## Module structure

- `app/main.py` — FastAPI routes
- `app/schemas.py` — request/response Pydantic schemas
- `app/service.py` — `HRISSyncManagementService` (tenant-scoped facade)
- `src/models.py` — dataclasses for users, departments, roles, sync jobs
- `src/service.py` — core `HRISSyncService` orchestrating field mappings and job scheduling
- `tests/test_hris_sync_service.py` — unit coverage

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8095
```

## Run tests

```bash
cd backend/services/hris-sync-service
python -m unittest discover -s tests
```
