> **DEPRECATED** — Superseded by: `docs/specs/SPEC_07_cohort_service.md`
> Reason: SPEC_ prefixed doc is the canonical spec. This legacy spec is retained for historical reference only.
> Last reviewed: 2026-04-04

cohort_operation | inputs | outputs
--- | --- | ---
cohort_creation | tenant_id, program_id, cohort_name, description, start_date, end_date, capacity, delivery_mode (self_paced/instructor_led/blended), timezone, facilitator_ids, enrollment_rules (optional), metadata (optional tags/attributes) | cohort_id, cohort_status (draft/active/scheduled), normalized_schedule_window, assigned_facilitators, enrollment_rule_set_id (if dynamic rules configured), audit_event (`CohortCreated`)
member_assignment | cohort_id, assignment_mode (manual/rule_based/bulk_import), learner_ids (manual), rule_definition (dynamic attributes), import_file_reference (bulk), assigned_by, effective_date, override_flags (allow_duplicates, prerequisites_override) | membership_records (cohort_membership_id, learner_id, state), assignment_summary (assigned/skipped/failed counts), conflict_report (capacity, eligibility, duplicates), waitlist_entries (if full), audit_event (`CohortMembersAssigned`)
schedule_management | cohort_id, session_plan (session_id, title, start_at, end_at, instructor_id, modality), milestone_dates (enrollment_cutoff, assignment_due_dates, assessments), recurrence_rules (optional), holiday_blackouts (optional), update_reason | published_cohort_calendar, learner_notifications_queue, updated_deadlines_by_member, schedule_version, conflict_warnings (instructor overlap, timezone collisions), audit_event (`CohortScheduleUpdated`)
