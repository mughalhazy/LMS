audit_event
trigger_service
data_logged

AdminActionExecuted
admin-portal-service
actor_user_id, actor_role, action_type, target_entity_type, target_entity_id, request_id, timestamp, source_ip, user_agent, outcome, reason_code

ConfigurationChanged
configuration-service
actor_user_id, actor_role, config_scope, config_key, previous_value_hash, new_value_hash, change_ticket_id, approval_reference, timestamp, source_ip

UserRoleUpdated
access-control-service
actor_user_id, subject_user_id, role_before, role_after, scope_type, scope_id, justification, approval_reference, timestamp, outcome

ComplianceControlEvaluated
compliance-service
control_id, control_name, evaluation_result, evaluated_entity_type, evaluated_entity_id, policy_version, evidence_reference, evaluator_id, timestamp

ComplianceExceptionGranted
compliance-service
actioned_by_user_id, exception_id, policy_id, subject_entity_type, subject_entity_id, reason, expires_at, approval_reference, timestamp

AuditLogExportRequested
audit-service
requestor_user_id, requestor_role, export_scope, date_range_start, date_range_end, export_format, legal_hold_flag, request_id, timestamp, outcome
