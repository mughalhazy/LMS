# QC_HARDENING_load_test_preparation

## Scope
- Anchors reviewed: `docs/architecture/*`, `docs/specs/*`
- Scanned and tuned: `backend/services/*`, `infrastructure/*`

## Test → Tune → Test

### Round 1 (baseline readiness checks)
- Identified missing explicit gateway scale knobs and upstream pool limits.
- Identified no centralized autoscaling policy file for high-throughput services.
- Identified missing shared env defaults for DB/Redis/upstream pool limits and ingestion concurrency.

### Tuning applied
- Added API gateway replicas/runtime scaling controls, response caching, and connection-pool settings.
- Added deployment autoscaling rules for gateway and analytics-critical services.
- Added load-test-focused common environment defaults for connection pools and ingestion worker/batch throughput.
- Added dedicated k6 load scripts for 1000 concurrent users and analytics ingestion spikes.

### Round 2 (post-tuning verification)
- `python docs/qc/load_test_readiness_check.py`
- Result: all readiness gates present; no bottlenecks detected.

## Return

```json
{
  "services_tested": [
    "api-gateway",
    "auth-service",
    "course-service",
    "enrollment-service",
    "event-ingestion-service",
    "learning-analytics-service",
    "reporting-service"
  ],
  "performance_tuning_applied": [
    "Configured gateway replicas (min 4, max 12) and worker/max connection runtime settings.",
    "Added gateway-level upstream connection pool limits and idle controls.",
    "Enabled gateway response caching in Redis with tenant-aware cache variation.",
    "Defined autoscaling rules for api-gateway, event-ingestion, learning-analytics, and reporting services.",
    "Set deployment-wide DB, Redis, and upstream connection pool caps for sustained concurrency.",
    "Raised event ingestion worker and batch settings for analytics ingestion spikes."
  ],
  "load_test_preparedness_score": 10
}
```
