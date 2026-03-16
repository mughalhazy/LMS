# Audit Logging Verification

## Scope
- Anchors reviewed:
  - `docs/specs/*`
  - `docs/architecture/security_architecture.md` (not present; used `docs/architecture/audit_logging.md` as closest available audit/security reference)
- Scan targets:
  - `backend/services/`
  - `infrastructure/observability/`

## Events Checked
- authentication events ✅
- role changes ✅
- course creation ✅
- assessment submissions ✅
- certificate issuance ✅
- admin actions ✅

## Required Audit Fields
All implemented audit events now include:
- `tenant_id`
- `actor_id`
- `timestamp`
- `destination` (set to `loki` for centralized logging target)

## Centralized Logging Verification
- OpenTelemetry Collector exports logs to Loki (`exporters.loki` + `service.pipelines.logs`).
- Promtail also forwards container logs to Loki.

## Validation Summary
- `events_logged`: 6/6 required categories
- `logging_fixes_applied`: Yes (audit middleware/logger modules and instrumentation added)
- `audit_logging_score`: 10/10
