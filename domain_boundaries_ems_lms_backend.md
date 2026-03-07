identity
Auth Service, User Profile Service, Role & Permission Service, Session/Token Service, SSO Federation Service
Owns authentication, authorization, identity lifecycle, account security, and federation with enterprise identity providers.

organization
Tenant Management Service, Organization Structure Service, Team/Cohort Service, Enrollment & Membership Service, Policy/Compliance Assignment Service
Owns multi-tenant org setup, hierarchical structures (business unit/department), memberships, and organization-level governance mappings.

learning
Learning Path Service, Course Lifecycle Service, Enrollment Orchestration Service, Progress Tracking Service, Certification Service
Owns learning journey orchestration from course assignment to completion, including paths, learner state, and credential issuance.

content
Content Repository Service, Content Authoring Service, Media/Asset Service, Content Versioning Service, Catalog & Discovery Service
Owns creation, storage, versioning, metadata, publishing, and discoverability of all learning assets.

assessment
Assessment Authoring Service, Quiz/Exam Delivery Service, Question Bank Service, Proctoring Interface Service, Grading & Feedback Service
Owns test construction and delivery, scoring workflows, item banks, and integrity controls for evaluative learning events.

analytics
Event Ingestion Service, Learning Data Warehouse Service, Reporting Service, Dashboard API Service, Insights/Segmentation Service
Owns telemetry collection, metrics modeling, learner/admin reporting, and analytical insights for outcomes and engagement.

integrations
API Gateway Adapter Service, HRIS Connector Service, CRM/ERP Connector Service, Notification Connector Service, Webhook/Event Bridge Service
Owns external system connectivity, data synchronization, outbound/inbound event contracts, and protocol translation.

AI
Recommendation Service, Skills Inference Service, Content Tagging/Classification Service, AI Tutor/Assistant Service, Generative Assessment Support Service
Owns ML/AI capabilities including personalization, skill graph inference, semantic enrichment, and AI-assisted learning interactions.

platform
Configuration Service, Workflow/Job Orchestrator Service, Notification Core Service, Audit & Logging Service, Observability/Feature Flag Service
Owns cross-cutting runtime capabilities (config, background jobs, notifications, auditing, reliability, and operational controls) used by all domains.
