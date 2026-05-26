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

> **Note:** This file is a historical service definition reference. The canonical service boundary map is `docs/architecture/microservice-boundary-map.md`. The canonical domain boundary map is `docs/architecture/ARCH_03_domain_service_architecture.md`.
