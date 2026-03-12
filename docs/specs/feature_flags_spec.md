flag_name | scope | rules
--- | --- | ---
tenant.feature.ai_recommendations | tenant | Default OFF for new tenants; can be enabled only by tenant_admin; must not impact other tenants; all evaluations must include tenant_id in targeting context.
tenant.feature.custom_branding | tenant | Default ON for enterprise plan tenants; read-only for non-entitled plans; plan entitlement check required before activation.
tenant.feature.advanced_analytics | tenant + role | Enable at tenant level first, then allow only roles in {tenant_admin, analyst, manager}; deny access for learners even if tenant-level flag is ON.
tenant.beta.new_dashboard | tenant + beta_cohort | Available only to tenants enrolled in beta program and users explicitly assigned to beta_cohort; requires acceptance of beta terms; auto-disable on beta end date unless promoted.
tenant.beta.ai_course_builder | tenant + beta_cohort + region | Restricted to approved beta tenants in supported regions; enforce data-processing notice acknowledgement before first use; log all usage events for beta review.
platform.rollout.mobile_nav_v2 | global + percentage + tenant_override | Progressive rollout using deterministic hashing of user_id (1% -> 5% -> 25% -> 50% -> 100%); emergency kill switch at global scope; tenant_override can force OFF.
platform.rollout.search_index_v3 | tenant + percentage + environment | Enable by environment order (dev, staging, prod); in prod start at 10% tenant traffic, increase only after SLO pass window; automatic rollback if error rate threshold exceeded.
platform.rollout.assessment_grading_engine_v2 | course_type + tenant + percentage | Roll out first to non-compliance courses, then compliance courses; exclude in-progress attempts from engine switching; once learner attempt starts, pin engine version for attempt lifetime.
