configuration_area | config_key | description | scope
--- | --- | --- | ---
branding | tenant.brand.name | Display name shown in headers, emails, certificates, and learner-facing pages. | tenant
branding | tenant.brand.logo_url | Primary logo asset used across web, mobile, and generated documents. | tenant
branding | tenant.brand.theme | Theme tokens (colors, typography, spacing) applied to UI components for tenant look-and-feel. | tenant
branding | tenant.brand.domain | Custom domain mapping for tenant-specific LMS access (e.g., learning.company.com). | tenant
language_localization | tenant.i18n.default_locale | Default locale used for first-time login and system-generated content. | tenant
language_localization | tenant.i18n.supported_locales | Allowed language/locale list available to users within the tenant. | tenant
language_localization | tenant.i18n.translation_override | Tenant-level override dictionary for labels, emails, and notifications. | tenant + locale
language_localization | tenant.i18n.date_time_format | Locale-specific date, time, and number formatting preferences. | tenant + locale
feature_flags | tenant.features.catalog_ai_recommendations | Enables/disables AI-based course recommendations for the tenant. | tenant
feature_flags | tenant.features.social_learning | Controls social features (discussion, peer comments, likes). | tenant
feature_flags | tenant.features.certification_expiry | Enables certification validity period and renewal workflows. | tenant
feature_flags | tenant.features.manager_dashboard | Toggles manager analytics and team learning oversight screens. | tenant + role
tenant_configuration | tenant.security.sso_provider | Identity provider configuration for SSO (SAML/OIDC metadata and mappings). | tenant
tenant_configuration | tenant.security.password_policy | Password complexity, rotation, and lockout policy for local accounts. | tenant
tenant_configuration | tenant.learning.default_enrollment_policy | Default enrollment mode (self-enroll, manager approval, admin assignment). | tenant
tenant_configuration | tenant.notifications.channel_policy | Global notification channel preferences (email/SMS/push) and throttling. | tenant
workflow_customization | tenant.workflow.enrollment_approval_chain | Defines approval sequence and escalation rules for enrollment requests. | tenant + organizational_unit
workflow_customization | tenant.workflow.recertification_cycle | Configures recertification intervals, grace periods, and reminder cadence. | tenant + program
workflow_customization | tenant.workflow.assignment_trigger_rules | Event-based assignment rules (hire date, role change, location transfer). | tenant + audience_segment
workflow_customization | tenant.workflow.completion_validation | Defines completion criteria (score threshold, attendance, manager sign-off). | tenant + course_type
compliance_rules | tenant.compliance.data_retention_policy | Retention windows and purge behavior for learning records and evidence logs. | tenant + region
compliance_rules | tenant.compliance.mandatory_training_matrix | Maps required courses to role/location/regulatory obligations. | tenant + jurisdiction + role
compliance_rules | tenant.compliance.audit_log_immutability | Sets audit-log write-once/retention controls for regulatory review. | tenant
compliance_rules | tenant.compliance.privacy_consent_requirements | Consent capture and re-consent requirements by legal basis and region. | tenant + region
