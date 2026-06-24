# revenue-service

Read-optimised revenue tracking and reporting. Ingests billing facts and builds per-tenant and per-capability daily aggregates. Design: `docs/designs/revenue-service-design.md` (B3P06).

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/revenue/facts` | Ingest revenue fact (triggers anomaly check) |
| GET | `/api/v1/revenue/tenants/{tenant_id}` | Daily tenant revenue query |
| GET | `/api/v1/revenue/capabilities/{key}` | Daily capability revenue query |
| GET | `/api/v1/revenue/capabilities/{key}?monthly=true` | Monthly roll-up (B15-005) |
| GET | `/api/v1/revenue/tenant-capability` | Tenant × capability revenue matrix (B15-005) |
| GET | `/api/v1/revenue/snapshots/{as_of_date}` | Immutable finance-close snapshot (B15-005) |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-005**: 3 missing endpoints added — tenant-capability matrix, immutable snapshots, monthly capability roll-up
- **B15-006**: BC-REV-01 anomaly detection — `revenue.anomaly.detected` emitted on fact ingest for 4 risk signals: overdue installments ≥7d, MoM revenue decline ≥15%, more signals extensible

## Gateway

Route: `/api/v1/revenue` | Rate limit: `public-api-standard`
