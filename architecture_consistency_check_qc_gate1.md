issue_type
component
description
severity
recommended_fix

Service map inconsistency
Service definitions (`define_service_map.md` vs `microservice_boundaries.md`)
Equivalent domains are named differently across architecture artifacts (e.g., `organization_catalog_service` vs `organization_tenant_service`, `content_delivery_service` vs `content_management_service`, `reporting_analytics_service` vs `analytics_reporting_service`). This prevents a single canonical service map and makes ownership/event routing ambiguous.
high
Create a canonical service catalog with immutable service IDs and aliases, then update all architecture docs to use the same IDs.

Domain boundary overlap
`user_profile_service` and `auth_identity_service`
`user_profile_service` owns `RoleAssignment` and department linkage while identity/auth services already own authorization and access boundaries. This overlaps bounded contexts and risks split-brain source of truth for permissions.
high
Move role/permission entities fully into identity/access domain; keep user profile bounded to person/employment/preferences metadata and reference role IDs only.

Event-service misalignment
Event architecture (`event_driven_architecture.md`, `define_event_domains.md`) vs LMS service map
Event producers/consumers are mostly HRIS/payroll-oriented (`employee-service`, `payroll-service`, `leave-service`, `expense-service`) and do not map to defined LMS microservices (`enrollment_service`, `assessment_service`, `progress_tracking_service`, etc.).
high
Split event catalogs by domain (EMS-HR vs LMS) or replace producer/consumer names with canonical LMS services for this architecture package.

Event ownership ambiguity
`TrainingEnrollmentAssigned` / `TrainingCourseCompleted`
Training events are produced by broad `learning-service`, but the service map decomposes learning into `enrollment_service`, `learning_path_service`, `progress_tracking_service`, and `certification_service`. Ownership is not aligned to bounded contexts.
medium
Assign each event to the owning microservice (e.g., assignment -> `enrollment_service`, completion -> `progress_tracking_service`, credential issuance -> `certification_service`) and enforce ownership via schema registry ACLs.

Tenant isolation inconsistency
`tenant_isolation_strategy.md` vs cloud/runtime architecture docs
Tenant strategy recommends a tiered model (default schema-per-tenant, optional database-per-tenant), but cloud architecture specifies single shared Aurora/Dynamo patterns without describing tenant tier routing, provisioning, or per-tenant deployment policies.
medium
Document and implement tenancy control-plane flows: tenant tier metadata, provisioning automation, DB routing strategy, migration paths, and observability/SLO segmentation by tenancy tier.
