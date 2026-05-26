# Monitoring and Observability Architecture

observability_component | tooling | purpose
--- | --- | ---
Metrics | Prometheus + OpenTelemetry Collector + Grafana | Collect service and infrastructure KPIs (latency, error rate, throughput, saturation, queue depth, job duration, DB performance), define SLO dashboards, and support capacity/performance analysis.
Logging | Fluent Bit + OpenSearch/Elasticsearch + Kibana (or Grafana Loki) | Centralize structured JSON logs with correlation IDs, enforce retention and PII redaction policies, enable fast incident triage, auditability, and root-cause analysis.
Tracing | OpenTelemetry SDK/Collector + Jaeger/Tempo | Capture distributed traces across LMS services and async event flows, visualize dependency paths, identify bottlenecks, and connect spans to logs/metrics via shared trace/span IDs.
Alerting | Alertmanager + Grafana Alerting + PagerDuty/Slack/Email | Trigger actionable alerts from SLO burn rates, symptom-based thresholds, and dead-letter/backlog anomalies; route by service ownership with escalation policies and on-call runbook links.
