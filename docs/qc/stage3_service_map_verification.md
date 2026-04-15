# Stage 3 Service Map Verification

## Scope

- Anchor references: `/docs/architecture/*`, `/docs/specs/*`, `/docs/api/*`, `/docs/data/*`, `/docs/integrations/*`, `/docs/qc/*`
- Scan target: `/backend/services/`

## expected_services

- identity_services:
  - /backend/services/auth-service
  - /backend/services/user-service
  - /backend/services/rbac-service
  - /backend/services/sso-service
- organization_services:
  - /backend/services/tenant-service
  - /backend/services/org-service
  - /backend/services/department-service
  - /backend/services/group-service
- course_services:
  - /backend/services/course-service
  - /backend/services/learning-path-service
  - /backend/services/cohort-service
- content_services:
  - /backend/services/content-service
  - /backend/services/lesson-service
  - /backend/services/media-service
  - /backend/services/scorm-service
- assessment_services:
  - /backend/services/assessment-service
  - /backend/services/quiz-engine
  - /backend/services/attempt-service
- enrollment_services:
  - /backend/services/enrollment-service
  - /backend/services/progress-service
  - /backend/services/prerequisite-engine-service
- certification_services:
  - /backend/services/certificate-service
  - /backend/services/badge-service
- analytics_services:
  - /backend/services/event-ingestion-service
  - /backend/services/learning-analytics-service
  - /backend/services/skill-analytics-service
  - /backend/services/reporting-service
- notification_services:
  - /backend/services/notification-service
  - /backend/services/email-service
  - /backend/services/push-service
- integration_services:
  - /backend/services/lti-service
  - /backend/services/hris-sync-service
  - /backend/services/webhook-service
  - /backend/services/api-key-service
- ai_services:
  - /backend/services/ai-tutor-service
  - /backend/services/course-generation-service
  - /backend/services/recommendation-service
  - /backend/services/skill-inference-service

## detected_services

- /backend/services/ai-tutor-service
- /backend/services/api-key-service
- /backend/services/assessment-service
- /backend/services/attempt-service
- /backend/services/auth-service
- /backend/services/badge-service
- /backend/services/certificate-service
- /backend/services/cohort-service
- /backend/services/content-service
- /backend/services/course-generation-service
- /backend/services/course-service
- /backend/services/department-service
- /backend/services/email-service
- /backend/services/enrollment-service
- /backend/services/event-ingestion-service
- /backend/services/group-service
- /backend/services/hris-sync-service
- /backend/services/learning-analytics-service
- /backend/services/learning-path-service
- /backend/services/lesson-service
- /backend/services/lti-service
- /backend/services/media-pipeline-service
- /backend/services/media-service
- /backend/services/notification-service
- /backend/services/org-service
- /backend/services/prerequisite-engine-service
- /backend/services/progress-service
- /backend/services/push-service
- /backend/services/quiz-engine
- /backend/services/rbac-service
- /backend/services/recommendation-service
- /backend/services/reporting-service
- /backend/services/scorm-runtime-service
- /backend/services/scorm-service
- /backend/services/skill-analytics-service
- /backend/services/skill-inference-service
- /backend/services/sso-service
- /backend/services/tenant-service
- /backend/services/user-service
- /backend/services/webhook-service

## missing_services

- None

## unexpected_services

- /backend/services/media-pipeline-service
- /backend/services/scorm-runtime-service

## naming_issues

- /backend/services/media-pipeline-service may be an adjacent/variant service name; expected map does not define this service
- /backend/services/scorm-runtime-service may be an adjacent/variant service name; expected map does not define this service

## misplaced_services

- None

## summary

- services_detected: 40
- verification_report_created: true
- architecture_alignment_status: partially_aligned
