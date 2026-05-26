# Domain Boundaries — LMS Backend

**Type:** Architecture Reference | **Last reviewed:** 2026-05-26

Domain-level boundary definitions for the LMS backend. Each domain owns the listed services and is responsible for the described concerns. Canonical boundary map: `docs/architecture/microservice-boundary-map.md`.

---

## identity
**Services:** Auth Service, User Profile Service, Role & Permission Service, Session/Token Service, SSO Federation Service
**Owns:** Authentication, authorization, identity lifecycle, account security, and federation with enterprise identity providers.

## organization
**Services:** Tenant Management Service, Organization Structure Service, Team/Cohort Service, Enrollment & Membership Service, Policy/Compliance Assignment Service
**Owns:** Multi-tenant org setup, hierarchical structures (business unit/department), memberships, and organization-level governance mappings.

## learning
**Services:** Learning Path Service, Course Lifecycle Service, Enrollment Orchestration Service, Progress Tracking Service, Certification Service
**Owns:** Learning journey orchestration from course assignment to completion, including paths, learner state, and credential issuance.

## content
**Services:** Content Repository Service, Content Authoring Service, Media/Asset Service, Content Versioning Service, Catalog & Discovery Service
**Owns:** Creation, storage, versioning, metadata, publishing, and discoverability of all learning assets.

## assessment
**Services:** Assessment Authoring Service, Quiz/Exam Delivery Service, Question Bank Service, Proctoring Interface Service, Grading & Feedback Service
**Owns:** Test construction and delivery, scoring workflows, item banks, and integrity controls for evaluative learning events.

## analytics
**Services:** Event Ingestion Service, Learning Data Warehouse Service, Reporting Service, Dashboard API Service, Insights/Segmentation Service
**Owns:** Telemetry collection, metrics modeling, learner/admin reporting, and analytical insights for outcomes and engagement.

## integrations
**Services:** API Gateway Adapter Service, HRIS Connector Service, CRM/ERP Connector Service, Notification Connector Service, Webhook/Event Bridge Service
**Owns:** External system connectivity, data synchronization, outbound/inbound event contracts, and protocol translation.

## AI
**Services:** Recommendation Service, Skills Inference Service, Content Tagging/Classification Service, AI Tutor/Assistant Service, Generative Assessment Support Service
**Owns:** ML/AI capabilities including personalization, skill graph inference, semantic enrichment, and AI-assisted learning interactions.

## platform
**Services:** Configuration Service, Workflow/Job Orchestrator Service, Notification Core Service, Audit & Logging Service, Observability/Feature Flag Service
**Owns:** Cross-cutting runtime capabilities (config, background jobs, notifications, auditing, reliability, and operational controls) used by all domains.

---

> **Note:** This file is a historical domain boundary reference. The canonical boundary map is `docs/architecture/microservice-boundary-map.md`.
