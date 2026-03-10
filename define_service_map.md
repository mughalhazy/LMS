# Enterprise LMS Backend Service Map for LMS

auth_identity_service  
responsibility: Manages user authentication, SSO/OAuth2 integration, token issuance/validation, and credential lifecycle.  
primary_entities: UserCredential, IdentityProvider, AccessToken, RefreshToken, Session

user_profile_service  
responsibility: Owns employee learner profiles, role affiliations, department linkage, and account status metadata.  
primary_entities: UserProfile, RoleAssignment, Department, EmploymentStatus

organization_catalog_service  
responsibility: Maintains organizational structure and learning audience group definitions used for targeting and access policies.  
primary_entities: BusinessUnit, Team, Location, LearnerGroup

course_catalog_service  
responsibility: Manages course metadata, catalog taxonomy, publish state, and discoverability attributes.  
primary_entities: Course, CourseCategory, Tag, CatalogListing

content_delivery_service  
responsibility: Serves learning assets and tracks content version references for secure playback/download access.  
primary_entities: LearningAsset, ContentVersion, ContentManifest, AssetAccessGrant

learning_path_service  
responsibility: Defines sequenced curricula and prerequisite relationships across courses and modules.  
primary_entities: LearningPath, PathNode, PrerequisiteRule, CurriculumAssignment

enrollment_service  
responsibility: Handles learner-to-course/path enrollment lifecycle including approvals, waitlists, and enrollment state transitions.  
primary_entities: Enrollment, EnrollmentRequest, WaitlistEntry, EnrollmentStatus

assessment_service  
responsibility: Manages quizzes/exams, attempt evaluation rules, scoring records, and pass/fail determination.  
primary_entities: Assessment, QuestionItem, AssessmentAttempt, ScoreRecord

progress_tracking_service  
responsibility: Captures learner activity events and computes completion/progress metrics at module, course, and path levels.  
primary_entities: LearningEvent, ProgressSnapshot, CompletionRecord, TimeSpentLog

certification_service  
responsibility: Issues and revokes certifications/badges based on completion and policy criteria, including expiration tracking.  
primary_entities: Certification, Badge, IssuanceRecord, ExpirationPolicy

notification_service  
responsibility: Sends transactional learning communications (enrollment, reminders, due dates, completions) across supported channels.  
primary_entities: NotificationTemplate, NotificationMessage, DeliveryChannel, DeliveryReceipt

reporting_analytics_service  
responsibility: Produces operational and compliance reports from curated learning data marts and KPI aggregates.  
primary_entities: ReportDefinition, ReportRun, KPIAggregate, ComplianceSnapshot
