operation | input_data | result
--- | --- | ---
create_tenant | tenant_name, tenant_code, primary_domain, admin_user, data_residency_region, subscription_plan | Creates a new tenant with unique tenant_id, initializes isolated data namespace, provisions default roles/settings, and returns tenant_id + bootstrap status.
validate_tenant_creation_request | tenant_code, primary_domain, admin_email, requested_region | Validates uniqueness, policy compliance, and regional eligibility; returns validation_passed and structured error list if blocked.
initialize_tenant_configuration | tenant_id, default_locale, timezone, branding, enabled_modules, security_baseline | Applies baseline configuration profile for the tenant and records configuration_version=1.
update_tenant_configuration | tenant_id, config_patch, actor_id, change_reason | Applies versioned configuration changes with audit log entry and returns updated configuration_version + effective_settings.
get_tenant_configuration | tenant_id, config_scope(optional), include_effective_defaults(boolean) | Returns current tenant configuration (raw and/or merged with platform defaults) with version metadata.
manage_tenant_feature_flags | tenant_id, feature_flag_changes, rollout_strategy, actor_id | Enables/disables tenant-scoped capabilities with optional staged rollout; returns updated flag states and activation timestamps.
suspend_tenant | tenant_id, suspension_reason, suspended_by, effective_at | Moves tenant lifecycle_state to suspended, blocks new sessions/writes per policy, and returns suspension_receipt.
reactivate_tenant | tenant_id, reactivation_reason, approved_by, effective_at | Restores tenant from suspended to active, re-enables permitted services, and returns reactivation_receipt.
archive_tenant | tenant_id, archive_policy, retention_period, requested_by | Transitions tenant to archived state, locks mutable operations, and schedules retention-bound data archival tasks.
decommission_tenant | tenant_id, legal_hold_status, purge_after_date, approved_by | Executes end-of-life workflow: verifies holds/retention, exports required records, purges tenant data at eligible date, and returns decommission_status.
get_tenant_lifecycle_status | tenant_id | Returns lifecycle_state, state_history, pending_transitions, policy_constraints, and next_allowed_actions.
