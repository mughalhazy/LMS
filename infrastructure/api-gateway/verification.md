# API Gateway Verification

## Backend service exposure check
| service | gateway prefix route | status |
|---|---|---|
| ai-tutor-service | /api/v1/ai-tutor | ✅ registered in `gateway.yaml` + `routes.yaml` |
| api-key-service | /api/v1/api-key | ✅ registered in `gateway.yaml` + `routes.yaml` |
| assessment-service | /api/v1/assessment | ✅ registered in `gateway.yaml` + `routes.yaml` |
| attempt-service | /api/v1/attempt | ✅ registered in `gateway.yaml` + `routes.yaml` |
| auth-service | /api/v1/auth | ✅ registered in `gateway.yaml` + `routes.yaml` |
| badge-service | /api/v1/badge | ✅ registered in `gateway.yaml` + `routes.yaml` |
| certificate-service | /api/v1/certificate | ✅ registered in `gateway.yaml` + `routes.yaml` |
| cohort-service | /api/v1/cohort | ✅ registered in `gateway.yaml` + `routes.yaml` |
| content-service | /api/v1/content | ✅ registered in `gateway.yaml` + `routes.yaml` |
| course-generation-service | /api/v1/course-generation | ✅ registered in `gateway.yaml` + `routes.yaml` |
| course-service | /api/v1/course | ✅ registered in `gateway.yaml` + `routes.yaml` |
| department-service | /api/v1/department | ✅ registered in `gateway.yaml` + `routes.yaml` |
| email-service | /api/v1/email | ✅ registered in `gateway.yaml` + `routes.yaml` |
| enrollment-service | /api/v1/enrollment | ✅ registered in `gateway.yaml` + `routes.yaml` |
| event-ingestion-service | /api/v1/event-ingestion | ✅ registered in `gateway.yaml` + `routes.yaml` |
| group-service | /api/v1/group | ✅ registered in `gateway.yaml` + `routes.yaml` |
| hris-sync-service | /api/v1/hris-sync | ✅ registered in `gateway.yaml` + `routes.yaml` |
| learning-analytics-service | /api/v1/learning-analytics | ✅ registered in `gateway.yaml` + `routes.yaml` |
| learning-path-service | /api/v1/learning-path | ✅ registered in `gateway.yaml` + `routes.yaml` |
| lesson-service | /api/v1/lesson | ✅ registered in `gateway.yaml` + `routes.yaml` |
| lti-service | /api/v1/lti | ✅ registered in `gateway.yaml` + `routes.yaml` |
| media-service | /api/v1/media | ✅ registered in `gateway.yaml` + `routes.yaml` |
| notification-service | /api/v1/notification | ✅ registered in `gateway.yaml` + `routes.yaml` |
| org-service | /api/v1/org | ✅ registered in `gateway.yaml` + `routes.yaml` |
| prerequisite-engine-service | /api/v1/prerequisite-engine | ✅ registered in `gateway.yaml` + `routes.yaml` |
| progress-service | /api/v1/progress | ✅ registered in `gateway.yaml` + `routes.yaml` |
| push-service | /api/v1/push | ✅ registered in `gateway.yaml` + `routes.yaml` |
| quiz-engine | /api/v1/quiz-engine | ✅ registered in `gateway.yaml` + `routes.yaml` |
| rbac-service | /api/v1/rbac | ✅ registered in `gateway.yaml` + `routes.yaml` |
| recommendation-service | /api/v1/recommendation | ✅ registered in `gateway.yaml` + `routes.yaml` |
| reporting-service | /api/v1/reporting | ✅ registered in `gateway.yaml` + `routes.yaml` |
| scorm-service | /api/v1/scorm | ✅ registered in `gateway.yaml` + `routes.yaml` |
| skill-analytics-service | /api/v1/skill-analytics | ✅ registered in `gateway.yaml` + `routes.yaml` |
| skill-inference-service | /api/v1/skill-inference | ✅ registered in `gateway.yaml` + `routes.yaml` |
| sso-service | /api/v1/sso | ✅ registered in `gateway.yaml` + `routes.yaml` |
| tenant-service | /api/v1/tenant | ✅ registered in `gateway.yaml` + `routes.yaml` |
| user-service | /api/v1/user | ✅ registered in `gateway.yaml` + `routes.yaml` |
| webhook-service | /api/v1/webhook | ✅ registered in `gateway.yaml` + `routes.yaml` |

## API spec route matching check
| Source spec | Route pattern | Target service |
|---|---|---|
| docs/api/core_rest_api.md | /api/v1/users, /api/v1/users/{userId} | user-service |
| docs/api/core_rest_api.md | /api/v1/courses, /api/v1/courses/{courseId} | course-service |
| docs/api/core_rest_api.md | /api/v1/lessons, /api/v1/lessons/{lessonId} | lesson-service |
| docs/api/core_rest_api.md | /api/v1/enrollments, /api/v1/enrollments/{enrollmentId} | enrollment-service |
| docs/api/core_rest_api.md | /api/v1/assessments, /api/v1/assessments/{assessmentId} | assessment-service |
| docs/api/core_rest_api.md | /api/v1/certificates, /api/v1/certificates/{certificateId} | certificate-service |
| docs/api/content_api.md | /api/v1/content/uploads | content-service |
| docs/api/content_api.md | /api/v1/courses/{courseId}/lessons | lesson-service |
| docs/api/content_api.md | /api/v1/courses/{courseId}/publish | course-service |
| docs/api/integration_api.md | /api/v1/integrations/hris/employees/sync | hris-sync-service |
| docs/api/integration_api.md | /api/v1/integrations/crm/contacts/upsert | org-service |
| docs/api/integration_api.md | /api/v1/integrations/lti/launch | lti-service |
| docs/api/integration_api.md | /api/v1/integrations/webhooks/events | webhook-service |
| docs/api/analytics_api.md | /api/v1/analytics/learners/{learnerId}/progress | learning-analytics-service |
| docs/api/analytics_api.md | /api/v1/analytics/courses/{courseId}/performance | learning-analytics-service |
| docs/api/analytics_api.md | /api/v1/analytics/skills | skill-analytics-service |
| docs/api/analytics_api.md | /api/v1/analytics/compliance/reports | reporting-service |
