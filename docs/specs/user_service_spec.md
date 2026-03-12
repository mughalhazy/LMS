# User Management Service Specification

operation | input_fields | result
--- | --- | ---
create_user_account | tenant_id, email, username, first_name, last_name, role_set, auth_provider, external_subject_id (optional), created_by | Creates a new user in `pending_activation` or `active` state (based on policy), assigns immutable user_id, and emits `user.created` lifecycle event.
activate_user_account | user_id, tenant_id, activation_token or admin_override_reason, activated_by | Moves user from `pending_activation` to `active`, records activation timestamp, and emits `user.activated` event.
update_user_profile | user_id, tenant_id, profile_fields (name, locale, timezone, title, department, manager_id, avatar_url), updated_by | Persists profile changes with version increment, updates search index, and emits `user.profile_updated` event.
manage_profile_preferences | user_id, tenant_id, notification_preferences, accessibility_preferences, language_preference, updated_by | Stores user-level preferences and returns normalized preference document for downstream notification and UI services.
change_account_status | user_id, tenant_id, target_status (`active`/`suspended`/`locked`/`deactivated`), reason_code, effective_at, changed_by | Applies account status transition if valid by policy/state machine, writes audit record, and emits `user.status_changed` event.
lock_or_unlock_account | user_id, tenant_id, action (`lock`/`unlock`), reason_code, lock_duration (optional), performed_by | Locks account after risk/compliance trigger or unlocks after review; updates authentication eligibility and returns current status.
terminate_or_reinstate_user | user_id, tenant_id, action (`terminate`/`reinstate`), offboarding_date, data_retention_policy_id, performed_by | Handles lifecycle end/re-entry: revokes sessions/access on terminate, preserves records per policy, and optionally restores prior entitlements on reinstate.
map_external_identity | user_id, tenant_id, identity_provider, external_subject_id, external_username (optional), mapping_attributes, mapped_by | Creates or updates authoritative identity mapping used for SSO/federation; enforces uniqueness of `(tenant_id, identity_provider, external_subject_id)`.
unmap_external_identity | user_id, tenant_id, identity_provider, external_subject_id, unmapped_by, reason | Removes or disables external identity link, optionally requiring alternate login credential before completion.
get_user_identity_links | user_id, tenant_id | Returns all linked identity mappings (provider, subject, status, last_login_at, assurance_level) for admin/security review.
get_user_lifecycle_timeline | user_id, tenant_id, include_audit (boolean) | Returns ordered lifecycle history (created, invited, activated, suspended, reactivated, terminated) with actor and timestamps.
