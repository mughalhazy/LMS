# HRIS Sync Service

Implements LMS HRIS synchronization capabilities described in `docs/integrations/hris_sync_spec.md`:

- **employee sync**: maps HRIS employees into LMS user entities
- **org hierarchy sync**: maps departments and parent-child structure
- **role mapping**: maps HRIS role catalog and permission bundles
- **scheduled sync jobs**: defines and executes due sync jobs on configured intervals

## Core module

- `src/models.py`: dataclasses for users, departments, roles, and sync jobs
- `src/service.py`: in-memory sync service orchestrating all mappings and job scheduling
- `tests/test_hris_sync_service.py`: unit coverage for all implemented sync flows

## Run tests

```bash
cd backend/services/hris-sync-service
python -m unittest discover -s tests
```
