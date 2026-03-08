auth_identity_service
responsibility: Owns authentication, authorization, SSO federation, session lifecycle, and credential security for all LMS actors.
key_entities: UserCredential, IdentityProvider, Session, AccessToken, PermissionPolicy

organization_tenant_service
responsibility: Owns tenant setup, organization hierarchy, learner groups, and membership relationships used for scoping access and assignments.
key_entities: Tenant, OrganizationUnit, Team, LearnerGroup, Membership

user_profile_service
responsibility: Owns learner and administrator profile data, employment attributes, preferences, and status independent from authentication.
key_entities: UserProfile, EmploymentRecord, RoleAssignment, Preference, AccountStatus

course_catalog_service
responsibility: Owns course metadata, taxonomy, publishing state, and discoverability in the LMS catalog.
key_entities: Course, CatalogCategory, Tag, CatalogListing, PublishState

content_management_service
responsibility: Owns learning asset storage, versioning, packaging, and content distribution contracts.
key_entities: LearningAsset, ContentVersion, ContentPackage, MediaFile, AssetManifest

learning_path_service
responsibility: Owns curriculum composition, sequencing rules, prerequisites, and path-level assignment logic.
key_entities: LearningPath, PathNode, PrerequisiteRule, CurriculumAssignment, PathMilestone

enrollment_service
responsibility: Owns enrollment lifecycle for courses and paths, including approvals, waitlists, due dates, and state transitions.
key_entities: Enrollment, EnrollmentRequest, WaitlistEntry, EnrollmentPolicy, EnrollmentStatus

assessment_service
responsibility: Owns assessment authoring, delivery, attempt evaluation, scoring, and feedback outcomes.
key_entities: Assessment, QuestionBankItem, AssessmentAttempt, ScoreRecord, FeedbackArtifact

progress_tracking_service
responsibility: Owns ingestion of learner activity signals and computation of progress/completion across assets, courses, and paths.
key_entities: LearningEvent, ProgressSnapshot, CompletionRecord, TimeSpentLog, MilestoneStatus

certification_service
responsibility: Owns credential issuance, badge management, renewals, expirations, and revocation policies.
key_entities: Certification, Badge, IssuanceRecord, RenewalRule, ExpirationPolicy

notification_service
responsibility: Owns messaging orchestration for LMS events across email, push, and in-app channels.
key_entities: NotificationTemplate, NotificationMessage, DeliveryChannel, DeliveryReceipt, NotificationPreference

analytics_reporting_service
responsibility: Owns analytics models, KPI computation, compliance reporting, and dashboard-ready aggregates.
key_entities: ReportDefinition, KPIAggregate, ComplianceSnapshot, DashboardMetric, DataMart

integration_gateway_service
responsibility: Owns inbound/outbound integrations with HRIS/ERP/IdP systems, webhook handling, and schema translation.
key_entities: ConnectorConfig, SyncJob, WebhookSubscription, IntegrationEvent, MappingRule

audit_compliance_service
responsibility: Owns immutable audit trails, policy evidence, and regulator-ready activity logs across all services.
key_entities: AuditLog, PolicyEvent, EvidenceRecord, RetentionPolicy, AccessTrace
