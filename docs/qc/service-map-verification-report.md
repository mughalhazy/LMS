# Stage 3 Service Map Verification

**Location:** `Repo/docs/qc/service-map-verification-report.md` | **Type:** QC Report | **Last reviewed:** 2026-05-26

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
- platform_services:
  - /backend/services/integration-service
  - /backend/services/payment-service
  - /backend/services/subscription-service
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
- /backend/services/integration-service
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
- /backend/services/payment-service
- /backend/services/scorm-service
- /backend/services/subscription-service
- /backend/services/skill-analytics-service
- /backend/services/skill-inference-service
- /backend/services/sso-service
- /backend/services/tenant-service
- /backend/services/user-service
- /backend/services/webhook-service

## missing_services

- None

## unexpected_services

- None

## naming_issues

- None

## misplaced_services

- None

## summary

- services_detected: 41
- verification_report_created: true
- architecture_alignment_status: partial — 3 services (integration-service, payment-service, subscription-service) exist on disk with no gateway registration and no prior catalogue entry; READMEs created 2026-05-26
- audit_correction_note_2026_05_26: Previous version incorrectly listed media-pipeline-service and scorm-runtime-service as standalone detected services. These are module paths inside media-service and scorm-service respectively — not top-level service directories. They have been removed. integration-service, payment-service, and subscription-service confirmed as real top-level services and added to expected_services.
