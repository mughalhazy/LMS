event_type
data_fields
aggregation_strategy

LearningActivityCaptured
activity_id, learner_id, course_id, module_id, activity_type, activity_status, device_type, platform, event_timestamp, session_id, duration_seconds
Stream ingestion into hourly activity fact tables; aggregate daily active learners, activity completion counts, and average session duration by course/module/platform.

ContentInteractionRecorded
interaction_id, learner_id, content_id, content_type, interaction_action, percent_consumed, playback_position_seconds, event_timestamp
Windowed aggregation (15-minute and daily) for interaction depth metrics; compute completion funnels and median consumption percent by content type.

AssessmentAttemptSubmitted
attempt_id, learner_id, assessment_id, course_id, attempt_number, score, max_score, passed_flag, submitted_at, time_spent_seconds
Incremental batch aggregation into daily assessment performance marts; calculate pass rate, average score, and retry distribution by assessment/course.

ProgressSnapshotUpdated
snapshot_id, learner_id, course_id, learning_path_id, progress_percent, completed_modules, total_modules, overdue_flag, snapshot_timestamp
SCD Type 2 snapshot history plus daily latest-state rollups; aggregate course/path completion rates and overdue learner counts.

CourseCompletionRecorded
completion_id, learner_id, course_id, completion_timestamp, total_time_spent_seconds, completion_source, certificate_issued_flag
Daily and monthly completion aggregates by learner cohort and course; compute completion velocity and median time-to-complete.

PathMilestoneAchieved
milestone_event_id, learner_id, learning_path_id, milestone_id, milestone_order, achieved_at, days_from_assignment
Cohort-based milestone progression curves using cumulative daily aggregates; calculate drop-off points between milestones.

CohortAssignmentCreated
cohort_assignment_id, cohort_id, learner_id, assignment_type, assigned_entity_id, assigned_at, due_date, assignment_source
Maintain cohort-assignment dimensional model; aggregate assignment load, due-date distribution, and assignment-to-start conversion rates per cohort.

CohortEngagementMeasured
engagement_event_id, cohort_id, learner_id, active_flag, sessions_count, active_minutes, period_start, period_end
Periodic (daily/weekly) cohort engagement cubes; compute WAU/MAU, engagement intensity, and inactivity risk segments per cohort.

SkillEvidenceLogged
skill_event_id, learner_id, skill_id, evidence_type, evidence_source_id, proficiency_delta, confidence_score, validated_flag, event_timestamp
Event-sourced skill ledger with daily proficiency snapshots; aggregate skill gain trends and validation ratios by skill/domain.

SkillProficiencyUpdated
proficiency_update_id, learner_id, skill_id, previous_level, new_level, update_reason, updated_at, assessor_type
Daily upsert into learner-skill fact table; compute proficiency distribution, level-transition rates, and net skill growth over time.

SkillGapIdentified
skill_gap_id, learner_id, role_id, required_skill_id, required_level, current_level, gap_size, detected_at
Nightly gap analysis aggregates by role/cohort; rank top missing skills and track gap-closure rate week over week.

RecommendationEngaged
recommendation_event_id, learner_id, recommendation_id, recommended_entity_id, skill_id, engagement_action, engaged_at
Attribution aggregation pipeline linking recommendation exposure to downstream learning actions; compute recommendation CTR and skill-impact lift.
