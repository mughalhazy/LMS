> NOTE: docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md is the canonical service inventory with correct service names and counts.
> This document provides architectural context only. For service names and coverage, use DOCUMENTATION_COVERAGE_MATRIX.md.
> Last reviewed: 2026-06-22

# Enterprise LMS Backend Service Map

**Type:** Architecture Reference | **Last reviewed:** 2026-05-26

Service responsibility definitions for the LMS backend. Each entry defines a service's responsibility boundary and primary entities. Canonical service boundary map: `docs/architecture/microservice-boundary-map.md`.

---

## auth_identity_service
**Responsibility:** Manages user authentication, SSO/OAuth2 integration, token issuance/validation, and credential lifecycle.
**Primary entities:** UserCredential, IdentityProvider, AccessToken, RefreshToken, Session

## user_profile_service
**Responsibility:** Owns employee learner profiles, role affiliations, department linkage, and account status metadata.
**Primary entities:** UserProfile, RoleAssignment, Department, EmploymentStatus

## organization_catalog_service
**Responsibility:** Maintains organizational structure and learning audience group definitions used for targeting and access policies.
**Primary entities:** BusinessUnit, Team, Location, LearnerGroup

## course_catalog_service
**Responsibility:** Manages course metadata, catalog taxonomy, publish state, and discoverability attributes.
**Primary entities:** Course, CourseCategory, Tag, CatalogListing

## content_delivery_service
**Responsibility:** Serves learning assets and tracks content version references for secure playback/download access.
**Primary entities:** LearningAsset, ContentVersion, ContentManifest, AssetAccessGrant

## learning_path_service
**Responsibility:** Defines sequenced curricula and prerequisite relationships across courses and modules.
**Primary entities:** LearningPath, PathNode, PrerequisiteRule, CurriculumAssignment

## enrollment_service
**Responsibility:** Handles learner-to-course/path enrollment lifecycle including approvals, waitlists, and enrollment state transitions.
**Primary entities:** Enrollment, EnrollmentRequest, WaitlistEntry, EnrollmentStatus

## assessment_service
**Responsibility:** Manages quizzes/exams, attempt evaluation rules, scoring records, and pass/fail determination.
**Primary entities:** Assessment, QuestionItem, AssessmentAttempt, ScoreRecord

## progress_tracking_service
**Responsibility:** Captures learner activity events and computes completion/progress metrics at module, course, and path levels.
**Primary entities:** LearningEvent, ProgressSnapshot, CompletionRecord, TimeSpentLog

## certification_service
**Responsibility:** Issues and revokes certifications/badges based on completion and policy criteria, including expiration tracking.
**Primary entities:** Certification, Badge, IssuanceRecord, ExpirationPolicy

## notification_service
**Responsibility:** Sends transactional learning communications (enrollment, reminders, due dates, completions) across supported channels.
**Primary entities:** NotificationTemplate, NotificationMessage, DeliveryChannel, DeliveryReceipt

## reporting_analytics_service
**Responsibility:** Produces operational and compliance reports from curated learning data marts and KPI aggregates.
**Primary entities:** ReportDefinition, ReportRun, KPIAggregate, ComplianceSnapshot

---

## V2 — Current Service Directory Names (2026-05-30)

Mapping from V1 logical names above to the actual folder names under `Repo/backend/services/`:

| V1 logical name | V2 directory name | Domain |
|---|---|---|
| auth_identity_service | `auth-service` + `sso-service` | Auth / Identity |
| user_profile_service | `user-service` | User Profile |
| organization_catalog_service | `org-service` + `department-service` + `group-service` | Org Hierarchy |
| course_catalog_service | `course-service` | Course Catalogue |
| content_delivery_service | `content-service` + `media-service` + `scorm-service` + `lti-service` | Content Delivery |
| learning_path_service | `learning-path-service` + `prerequisite-engine-service` | Learning Paths |
| enrollment_service | `enrollment-service` + `cohort-service` + `session-service` | Enrollment |
| assessment_service | `assessment-service` + `attempt-service` + `quiz-engine` + `exam-engine` | Assessment |
| progress_tracking_service | `progress-service` + `lesson-service` + `learning-analytics-service` + `skill-analytics-service` | Progress & Analytics |
| certification_service | `certificate-service` + `badge-service` | Credentials |
| notification_service | `notification-service` + `email-service` + `push-service` | Notifications |
| reporting_analytics_service | `reporting-service` + `analytics-service` | Reporting |
| _(not in V1)_ | `program-service` | Programs / Curriculum |
| _(not in V1)_ | `institution-service` | Institutions |
| _(not in V1)_ | `rbac-service` | RBAC / Authorization |
| _(not in V1)_ | `tenant-service` | Tenant Lifecycle |
| _(not in V1)_ | `config-service` | Configuration |
| _(not in V1)_ | `entitlement-service` | Entitlements |
| _(not in V1)_ | `feature-flag-service` | Feature Flags |
| _(not in V1)_ | `capability-registry` | Capability Registry |
| _(not in V1)_ | `usage-metering-service` | Usage Metering |
| _(not in V1)_ | `audit-policy-service` | Audit Policy |
| _(not in V1)_ | `workflow-engine` | Workflow Automation |
| _(not in V1)_ | `onboarding-service` | Tenant Onboarding |
| _(not in V1)_ | `enterprise-control-service` | Enterprise Control |
| _(not in V1)_ | `integration-service` + `hris-sync-service` + `webhook-service` | Integrations |
| _(not in V1)_ | `catalog-service` + `checkout-service` + `invoice-billing-service` + `subscription-service` + `payment-service` + `revenue-service` + `owner-economics-service` | Commerce |
| _(not in V1)_ | `financial-ledger-service` + `system-economics-service` | Financial |
| _(not in V1)_ | `ai-tutor-service` + `recommendation-service` + `skill-inference-service` | AI Services |
| _(not in V1)_ | `operations-os-service` + `interaction-layer-service` | Ops Intelligence |
| _(not in V1)_ | `offline-sync-service` | Offline Sync |
| _(not in V1)_ | `review-service` | Reviews & Ratings |
| _(not in V1)_ | `hr-helpdesk-service` | HR Helpdesk |
| _(not in V1)_ | `api-key-service` | API Key Management |
| _(not in V1)_ | `course-generation-service` | AI Course Generation |
| _(not in V1)_ | `event-ingestion-service` | Event Ingestion |

> **Note:** This file is a historical service definition reference. The canonical service boundary map is `docs/architecture/microservice-boundary-map.md`. The canonical domain boundary map is `docs/architecture/ARCH_03_domain_service_architecture.md`.
