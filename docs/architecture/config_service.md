> **DEPRECATED** — Superseded by: `docs/architecture/B2P01_config_service_design.md`
> Reason: BATCH doc is highest-priority and supersedes all general docs on the same topic.
> Last reviewed: 2026-04-04

# LMS Configuration Service Definition

| config_area | configuration_keys | usage |
| --- | --- | --- |
| tenant configuration | `tenant.id`, `tenant.name`, `tenant.region`, `tenant.timezone`, `tenant.locale.default`, `tenant.branding.theme`, `tenant.branding.logo_url`, `tenant.security.password_policy`, `tenant.sso.enabled`, `tenant.sso.idp_metadata_url` | Stores tenant-scoped identity, localization, branding, and security defaults used during tenant bootstrap, login experience rendering, and policy enforcement across LMS modules. |
| feature flags | `feature.learning_paths.enabled`, `feature.ai_copilot.enabled`, `feature.certifications.enabled`, `feature.manager_dashboard.enabled`, `feature.gamification.enabled`, `feature.notifications.push.enabled`, `feature.assessments.proctoring.enabled`, `feature.beta.course_authoring_v2.enabled` | Controls progressive rollout, tenant-specific enablement, and safe experimentation of LMS capabilities without redeploying services. |
| runtime configuration | `runtime.cache.ttl_seconds`, `runtime.job_retry.max_attempts`, `runtime.job_retry.backoff_ms`, `runtime.pagination.default_limit`, `runtime.pagination.max_limit`, `runtime.rate_limit.requests_per_minute`, `runtime.session.timeout_minutes`, `runtime.upload.max_file_size_mb`, `runtime.audit.log_level` | Defines operational behavior for APIs and workers at runtime, including performance tuning, retry policy, API guardrails, and audit verbosity. |
| environment variables | `ENV`, `CONFIG_SOURCE`, `DATABASE_URL`, `REDIS_URL`, `KAFKA_BROKERS`, `JWT_PUBLIC_KEY`, `KMS_KEY_ID`, `SMTP_HOST`, `SMTP_PORT`, `S3_BUCKET`, `OTEL_EXPORTER_OTLP_ENDPOINT` | Supplies deployment-specific secrets and infrastructure endpoints injected per environment (dev/stage/prod), allowing the same artifact to run across environments with externalized configuration. |
