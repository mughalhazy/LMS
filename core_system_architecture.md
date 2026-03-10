# LMS Backend System Architecture (Multi-tenant, Cloud-native, API-first, Event-driven)

| component | responsibility | dependencies |
|---|---|---|
| api_gateway | Single entry point for tenant-aware REST/GraphQL APIs, request routing, rate limiting, auth propagation, and API version management. | identity_access_service, tenant_context_service, service_mesh, observability_platform |
| identity_access_service | Handles OAuth2/OIDC, token issuance/validation, RBAC/ABAC policy enforcement, and service-to-service identity. | tenant_context_service, secrets_kms, policy_service |
| tenant_context_service | Resolves tenant metadata (tenant id, plan, region, feature flags), enforces hard tenant isolation boundaries, and injects tenant context into every request/event. | tenant_registry_db, config_feature_flag_service, service_mesh |
| lms_command_api_services | Domain microservices exposing API-first command/query endpoints (courses, enrollments, assessments, certifications, notifications) with strict per-tenant data ownership. | api_gateway, identity_access_service, tenant_context_service, transactional_datastores, cache_layer |
| event_bus_streaming_platform | Durable pub/sub backbone for domain events, async workflows, retries, DLQ handling, and cross-service integration. | schema_registry, tenant_context_service, lms_command_api_services, workflow_orchestrator |
| workflow_orchestrator | Runs long-lived, event-driven business processes (enrollment approval, reminder cadence, recertification lifecycle) using sagas/state machines. | event_bus_streaming_platform, lms_command_api_services, notification_service |
| notification_service | Sends email/SMS/push/webhook notifications from event subscriptions with tenant-level template/branding customization. | event_bus_streaming_platform, template_service, external_messaging_providers |
| analytics_ingestion_service | Consumes domain events and API snapshots into a tenant-partitioned analytical model for dashboards/compliance reporting. | event_bus_streaming_platform, object_storage_data_lake, warehouse_lakehouse |
| query_reporting_api | Provides read-optimized analytics/report APIs and scheduled report exports with row-level tenant security. | warehouse_lakehouse, cache_layer, identity_access_service |
| transactional_datastores | Polyglot operational persistence (tenant-partitioned SQL/NoSQL) for domain services with encryption, backups, and PITR. | secrets_kms, backup_recovery_service |
| cache_layer | Low-latency cache for tenant-scoped sessions, authorization decisions, catalog lookups, and hot query results. | lms_command_api_services, query_reporting_api |
| object_storage_data_lake | Immutable event/archive storage and batch processing substrate for historical analytics, audit, and reprocessing. | analytics_ingestion_service, data_governance_service |
| schema_registry | Governs versioned API/event contracts with compatibility checks to preserve API-first and event-driven evolution. | event_bus_streaming_platform, ci_cd_platform |
| service_mesh | Secure service-to-service networking (mTLS), traffic policies, retries, circuit breaking, and progressive delivery controls. | kubernetes_platform, observability_platform |
| kubernetes_platform | Cloud-native runtime for container orchestration, autoscaling, self-healing, and regional deployment topology. | cloud_infrastructure, ci_cd_platform |
| ci_cd_platform | Automated build/test/deploy pipelines with policy gates, contract tests, and canary/blue-green release strategies. | source_control, artifact_registry, schema_registry, kubernetes_platform |
| observability_platform | Centralized logs, metrics, traces, SLO monitoring, and tenant-aware operational telemetry. | service_mesh, kubernetes_platform, lms_command_api_services, event_bus_streaming_platform |
| data_governance_service | Manages audit trails, data retention, tenant data residency rules, and compliance controls (e.g., SOC2/GDPR). | object_storage_data_lake, transactional_datastores, identity_access_service |
| config_feature_flag_service | Centralized runtime configuration and per-tenant feature toggles enabling controlled rollout of APIs/events. | tenant_context_service, ci_cd_platform |
| disaster_recovery_resilience_service | Coordinates cross-region replication, failover orchestration, and resilience playbooks for critical LMS services. | transactional_datastores, object_storage_data_lake, kubernetes_platform, observability_platform |
