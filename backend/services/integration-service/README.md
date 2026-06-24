# Integration Service

Platform integration service — stateless capability decision orchestration.

## Design reference

`Repo/docs/designs/platform-integration-layer-design.md` | CGAP-078

## Pattern

Implements `B2P08 PlatformIntegrationAPI` — `StatelessDecisionOrchestrator`. All requests are evaluated through a 6-step pipeline:

1. Capability Registry lookup
2. Config Resolution
3. Entitlement Check
4. Feature Flag evaluation
5. Final Decision
6. Usage Metering emit

No state is held between requests. All inputs come from the calling service; all outputs are decision records.

## API routes

Authentication: JWT required (`Authorization: Bearer <token>`).

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/integration/evaluate` | Core B2P08 6-step capability decision — returns ALLOW/DENY/CONDITIONAL with trace |
| POST | `/api/integrations/hris/employees/sync` | HRIS employee sync — gated via capability evaluation |
| POST | `/api/integrations/crm/contacts/upsert` | CRM contact upsert — gated via capability evaluation |
| POST | `/api/integrations/lti/launch` | LTI launch routing — gated via capability evaluation |
| POST | `/api/integrations/webhooks/events` | Inbound webhook event ingestion — gated via capability evaluation |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

`openapi.yaml` in this directory is the legacy reference. `app/main.py` is the authoritative HTTP entrypoint (added 2026-06-01, B12-001).

## Status

HTTP entrypoint added 2026-06-01 (B12-001). Not yet registered in the API gateway (pending).
