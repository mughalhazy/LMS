progress_event
tracked_fields
consumer_services

LessonCompletionTracked
tenant_id, learner_id, course_id, lesson_id, enrollment_id, completion_status, score, time_spent_seconds, completed_at, attempt_count
analytics-service, recommendation-service, adaptive-learning-engine, learner-profile-service, notification-service

CourseCompletionTracked
tenant_id, learner_id, course_id, enrollment_id, completion_status, final_score, started_at, completed_at, total_time_spent_seconds, certificate_id
analytics-service, certification-service, recommendation-service, learner-profile-service, compliance-reporting-service, notification-service

LearningPathProgressUpdated
tenant_id, learner_id, learning_path_id, assigned_course_ids, completed_course_ids, progress_percentage, current_course_id, status, last_activity_at, expected_completion_date
analytics-service, recommendation-service, learner-profile-service, manager-dashboard-service, notification-service
