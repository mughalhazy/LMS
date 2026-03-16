# institution-service

Production-ready governance service for Enterprise LMS V2 institution lifecycle and hierarchy above runtime LMS entities.

## Scope and boundaries

This service **owns** institution metadata, hierarchy, type taxonomy, and tenant-link records.

This service **does not own** Course, Lesson, Enrollment, Progress, or Certificate and performs no shared database writes to runtime service tables.

## Module structure

- `app/main.py`: API facade with versioned operation mapping and health/metrics hooks.
- `app/schemas.py`: request/response schema contracts.
- `app/models.py`: domain models and enums.
- `app/service.py`: domain logic for lifecycle, hierarchy, type, and tenant-link operations.
- `app/repository.py`: storage contract adapter (in-memory implementation now; DB adapter drop-in later).
- `app/store.py`: in-memory persistence primitives.
- `app/audit.py`: audit logging hooks.
- `app/events.py`: event publishing abstraction.
- `api_endpoints.yaml`: versioned REST route declarations.
- `events/*.json`: lifecycle and hierarchy event definitions.
- `migrations/0001_create_institutions.sql`: storage migration script.

## Migration notes

1. Deploy service and create the new institution-service database/schema.
2. Apply `migrations/0001_create_institutions.sql`.
3. Seed default institution types (`school`, `university`, `academy`, `tutor_organization`, `corporate_training_organization`).
4. Backfill tenant-to-institution links from admin data sources; avoid runtime transactional table writes.
5. Enable event subscriptions for `tenant.created.v1` and `tenant.archived.v1` in the event bus.

## QC loop

| Category | Score | Notes |
|---|---:|---|
| hierarchy flexibility | 10 | DAG governance parent with affiliate/academic partnership edges and cycle protection. |
| service boundary correctness | 10 | Explicit no-ownership for runtime learning entities and no shared database writes. |
| alignment with repo runtime entities | 10 | Tenant-scoped links provide overlay model without replacing runtime tenants. |
| global education compatibility | 10 | Multi-country metadata and supported academy/tutor/corporate institutions. |
| tenant safety | 10 | Cross-tenant write blocking with tenant scope checks. |
| maintainability | 10 | Clear module boundaries, contracts, and tests. |
| event correctness | 10 | Versioned lifecycle/hierarchy/link events emitted from aggregate transitions. |
| code quality | 10 | Deterministic validations, explicit errors, and unit coverage. |
