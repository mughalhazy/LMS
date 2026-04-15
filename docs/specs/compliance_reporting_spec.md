report_name
data_sources
fields

Training Completion Report
lms_enrollments, lms_course_completions, learner_profiles, course_catalog
report_generated_at, learner_id, learner_name, department, manager_id, course_id, course_title, assignment_type, assigned_at, due_date, completion_status, completion_date, completion_percentage, days_to_complete, overdue_flag

Certification Validity Report
lms_certifications, certification_requirements, learner_profiles, recertification_rules, credential_expiry_events
report_generated_at, learner_id, learner_name, role, certification_id, certification_name, issuing_authority, issued_date, expiry_date, validity_status, days_until_expiry, recertification_required_flag, recertification_due_date, grace_period_end_date

Mandatory Training Compliance Report
mandatory_training_assignments, lms_course_completions, learner_profiles, policy_training_matrix, exemption_registry
report_generated_at, learner_id, learner_name, department, role, policy_id, mandatory_course_id, mandatory_course_title, assignment_date, due_date, completion_status, completion_date, exemption_flag, exemption_reason, non_compliance_flag, escalation_level
