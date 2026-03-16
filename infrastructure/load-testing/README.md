# LMS Load Testing Preparation

## Scripts

- `k6/lms_1000_users.js`: baseline mixed workload validating gateway and core API behavior for 1000 concurrent users.
- `k6/analytics_ingestion_spike.js`: ingestion-focused stress profile for analytics event spikes.

## Run

```bash
k6 run infrastructure/load-testing/k6/lms_1000_users.js
k6 run infrastructure/load-testing/k6/analytics_ingestion_spike.js
```

Optional environment variable:

- `BASE_URL` (default `http://localhost:8080`)

## Readiness gates

- p95 latency under 450ms for mixed API profile.
- p95 latency under 700ms for ingestion spike profile.
- Error rate below 1% in baseline, below 2% in spike scenario.
- Verify API gateway and event-ingestion services have autoscaling and tuned connection pools.
