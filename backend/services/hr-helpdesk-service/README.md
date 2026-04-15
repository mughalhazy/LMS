# HR Helpdesk Service

`hr-helpdesk-service` owns the tenant-scoped HR support workflow for employee questions and operational requests.

## Capabilities

- ticket intake and lifecycle management for HR cases
- priority scoring and queue ranking for advanced triage
- analytics snapshots covering backlog health, SLA risk, category mix, and automation effectiveness
- automation hooks that emit deterministic dispatch records when cases meet configured triggers

## API

Versioned endpoints are exposed under `/api/v1/hr-helpdesk`.

## Boundaries

- Owns HR helpdesk tickets, triage metadata, and automation dispatch records.
- Does **not** write into HRIS, notification, or workflow systems directly; integrations are modeled as automation hook dispatches.
- Stores all state inside service-local in-memory storage for this repo implementation.

## Local run

```bash
uvicorn app.main:app --reload --port 8039
```

## Test

```bash
cd backend/services/hr-helpdesk-service
pytest
```
