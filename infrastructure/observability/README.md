# LMS Observability Stack

This directory configures a centralized observability platform for LMS backend services, aligned to the core architecture requirement for centralized logs, metrics, traces, and operational telemetry.

## Components

- **Prometheus**: scrapes service `/metrics` endpoints and blackbox health probes.
- **Blackbox Exporter**: probes `/health` endpoints for each service.
- **OpenTelemetry Collector**: ingests OTLP telemetry from services and exports:
  - metrics to Prometheus
  - traces to Tempo
  - logs to Loki
- **Loki + Promtail**: centralized log aggregation.
- **Tempo**: distributed tracing backend.
- **Grafana**: pre-provisioned datasources and service-monitoring dashboard.

## Service inventory coverage

Targets for every service under `backend/services/` are declared in:

- `services/services-targets.json`
- `services/services-health-targets.json`

This ensures each service is represented for both metrics scraping and health monitoring.

## Local run

```bash
docker compose -f infrastructure/observability/docker-compose.yml up -d
```

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)
- Loki: `http://localhost:3100`
- Tempo: `http://localhost:3200`

## Verification

```bash
python infrastructure/observability/scripts/verify_observability.py
```

Expected output:

- `services_monitored=<count>`
- `metrics_collected=yes`
- `monitoring_score=10/10`
