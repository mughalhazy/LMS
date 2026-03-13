# QC Gate 4 — Service Communication Validation

prompt: QC_GATE_4_service_communication_validation
system: LMS

## Validation Scope

- anchors:
  - `/docs/architecture/*`
  - `/docs/specs/*`
  - `/docs/api/*`
  - `/docs/integrations/*`
  - `/docs/qc/*`
- scan paths:
  - `/backend/services/`
  - `/infrastructure/`

## Services Checked

- auth-service
- user-service
- course-service
- assessment-service
- enrollment-service
- learning-analytics-service (analytics-services)

## Findings

- service discovery used:
  - **pass** after fixes (`discovery://` lookup is codified in service discovery defaults and internal client matrix).
- no hardcoded service URLs:
  - **pass** after replacing gateway JWT JWKS endpoint with `discovery://auth-service/...`.
- internal service clients configured:
  - **pass** after adding explicit internal client contracts for all requested service communication paths.
- retry policies implemented:
  - **pass** via default and per-client `max_attempts` + `backoff_ms`.
- timeout handling implemented:
  - **pass** via default and per-client `timeout_ms`.

## Violations Fixed

1. Replaced direct gateway auth JWKS URL with service discovery URI.
2. Added missing canonical internal service-client communication contract for the checked services.
3. Added explicit retry and timeout policy entries for each checked internal client relationship.

## Final Result

- services_checked: 6
- violations_fixed: 3
- communication_score: 10/10
