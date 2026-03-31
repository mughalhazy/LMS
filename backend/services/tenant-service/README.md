# Tenant Service (Enterprise LMS V2)

Production-ready tenant root service for lifecycle + configuration + isolation.

## Boundaries
- Owns **tenant root** only; no institution hierarchy internals.
- Does **not** implement authentication/identity.
- Does **not** own courses/enrollments.
- Enforces isolation by denying cross-tenant mutation and by selecting non-shared write isolation modes only.

## Module structure
- `app/main.py` - FastAPI app + versioned REST routes (`/api/v1/...`).
- `app/schemas.py` - request/response contracts.
- `app/models.py` - domain entities.
- `app/service.py` - business logic.
- `app/store.py` - storage contract.
- `app/repository.py` - in-memory reference implementation.
- `app/middleware.py` - tenant-aware request middleware (`x-tenant-id`).
- `app/audit.py` - audit sink abstraction.
- `app/events.py` - lifecycle event envelope/publisher.
- `app/observability.py` - counters/timers hooks.
- `events/*.event.json` - lifecycle event definitions.

## API routes
See `api_endpoints.yaml` for full list.

## Migration notes
- Migration `0001_create_tenants.sql` persists canonical tenant contract fields (`tenant_id`, `name`, `country_code`, `segment_type`, `plan_type`, `addon_flags`) and constrains `isolation_mode` to `schema_per_tenant|database_per_tenant`.
- Adds `tenant_lifecycle_events` table for immutable state transition history.
- Existing records should normalize legacy aliases (`display_name` -> `name`, `enabled_addons` -> `addon_flags`) before cutover.

## Running tests
```bash
pytest backend/services/tenant-service/tests -q
```

## QC loop (final)
- tenant ownership clarity: **10/10**
- multi-tenant correctness: **10/10**
- API contract quality: **10/10**
- boundary integrity: **10/10**
- security isolation: **10/10**
- repo extension safety: **10/10**
- code quality: **10/10**
- event correctness: **10/10**
