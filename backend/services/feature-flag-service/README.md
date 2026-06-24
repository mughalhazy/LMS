# feature-flag-service

Runtime feature flag evaluation. Deterministic 7-step pipeline: kill_switch → entitlement_guard → segment_rule → tenant_override → experiment → default. Supports experimentation with weighted variant allocation. Design: `docs/designs/feature-flag-system-design.md` (B2P03).

## Evaluation precedence
`kill_switch > entitlement_denied > tenant_override > experiment > segment_rule > default`

## Gateway
Route: `/api/v1/flags` | Rate limit: `public-api-standard`
