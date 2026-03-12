# Reporting Engine Specification

| report | inputs | output_format |
|---|---|---|
| Scheduled Reports | `report_type` (completion, assessment, compliance, engagement), `schedule` (hourly/daily/weekly/monthly), `timezone`, `delivery_channel` (email/webhook/SFTP), `recipients`, `filters` (tenant, department, cohort, course, date_range) | JSON report payload for API/webhook delivery and CSV/XLSX/PDF attachments for scheduled distribution |
| Export Formats | `dataset` (learner_progress, course_performance, certification_status, audit_trail), `columns`, `filters`, `locale`, `file_format`, `compression` | CSV, XLSX, JSON, and PDF exports; optional ZIP packaging for large multi-file exports |
| Dashboard Feeds | `dashboard_id`, `widget_set`, `time_granularity` (real-time/hour/day/week), `dimensions`, `metrics`, `comparison_window`, `tenant_scope` | Low-latency JSON feed for dashboard widgets, with optional Parquet snapshots for downstream BI ingestion |
