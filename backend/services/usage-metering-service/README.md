# usage-metering-service

Event-driven capability usage ingestion and aggregation. Accepts canonical usage events, deduplicates, and builds hourly/daily/monthly rollups per tenant+capability. Exports daily aggregates for billing pipeline. Design: `docs/designs/usage-metering-service-design.md` (B2P04).

## Gateway
Route: `/api/v1/usage` | Rate limit: `event-ingestion-guarded`
