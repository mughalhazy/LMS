> **DEPRECATED** — Superseded by: `docs/specs/DOC_01_feature_inventory.md`
> Reason: SPEC doc is higher-priority. Note: "feature" = "capability" — see `docs/architecture/DOC_NORM_01_terminology_bridge.md`
> Last reviewed: 2026-04-04

# LMS Enterprise LMS Feature Inventory

| module | feature_name | description | primary_users |
|---|---|---|---|
| learning management | Course Catalog | Centralized searchable catalog with filters by topic, role, region, and language for all available learning content. | Learners, Managers, L&D Admins |
| learning management | Enrollment Management | Supports self-enrollment, manager assignment, admin assignment, and rule-based auto-enrollment into courses. | Learners, Managers, L&D Admins |
| learning management | Instructor-Led Training Scheduling | Creates and manages classroom/virtual session schedules, seat limits, waitlists, and attendance rosters. | Instructors, L&D Admins, Learners |
| learning management | Session Registration & Waitlists | Handles learner registration, waitlist prioritization, seat release, and registration notifications. | Learners, L&D Admins |
| learning management | Learning Record Tracking | Tracks starts, completions, time spent, and status changes at learner/course/session level. | Learners, Managers, L&D Admins |
| learning management | Learning Notifications | Sends configurable reminders, due-date alerts, assignment messages, and completion confirmations. | Learners, Managers, L&D Admins |
| learning management | Social/Collaborative Learning | Enables discussions, comments, likes, peer recommendations, and community engagement around content. | Learners, Instructors |
| learning management | Resource Library | Hosts downloadable job aids, templates, and reference assets linked to formal learning programs. | Learners, Instructors |
| course authoring | WYSIWYG Course Builder | Provides drag-and-drop authoring for text, media, interactions, and structure without coding. | Instructional Designers, SMEs |
| course authoring | SCORM/xAPI/AICC Packaging | Publishes interoperable course packages and statements for standards-based LMS and LRS tracking. | Instructional Designers, LMS Admins |
| course authoring | Multimedia Authoring | Supports embedding video, audio, slides, simulations, and interactive media in learning objects. | Instructional Designers, SMEs |
| course authoring | Question Bank Authoring | Creates reusable tagged question items with difficulty and objective metadata for assessments. | Instructional Designers, Instructors |
| course authoring | Content Version Control | Manages draft, review, publish, and rollback lifecycle with version history and audit trail. | Instructional Designers, L&D Admins |
| course authoring | Localization Workflow | Supports translation export/import, language variants, and locale-specific content publishing. | Localization Teams, Instructional Designers |
| course authoring | Content Templates | Provides reusable branded templates for course pages, lessons, quizzes, and certificates. | Instructional Designers |
| assessments | Quiz Engine | Delivers configurable assessments with multiple question types and grading rules. | Learners, Instructors |
| assessments | Assignment Submission | Accepts file, text, and project submissions with deadlines and submission status tracking. | Learners, Instructors |
| assessments | Proctoring Integration | Connects to online proctoring providers for identity checks, monitoring, and integrity flags. | Learners, Compliance Admins, Instructors |
| assessments | Adaptive Assessments | Adjusts question sequence/difficulty based on learner responses to improve measurement accuracy. | Learners, Instructors |
| assessments | Rubric-Based Grading | Enables standardized manual grading using configurable rubrics and feedback comments. | Instructors, Assessors |
| assessments | Retake & Attempt Policies | Configures attempt limits, cooldown periods, pass thresholds, and remediation conditions. | L&D Admins, Instructors |
| assessments | Plagiarism Detection | Integrates originality checking for written submissions and flags similarity risks. | Instructors, Compliance Admins |
| certifications | Certificate Issuance | Automatically generates branded digital certificates upon meeting completion and performance criteria. | Learners, L&D Admins |
| certifications | Recertification Management | Tracks certification validity windows and manages renewal requirements and expirations. | Learners, Compliance Admins, Managers |
| certifications | Expiry Notifications | Sends pre-expiry and overdue reminders to learners, managers, and compliance stakeholders. | Learners, Managers, Compliance Admins |
| certifications | Digital Badge Support | Issues verifiable badges with metadata for skill and achievement recognition. | Learners, Talent Leaders |
| certifications | External Validation | Supports certificate verification links/IDs for auditors, partners, and external stakeholders. | Auditors, Partners, Compliance Admins |
| learning paths | Path Builder | Creates sequenced learning journeys combining courses, assessments, and checkpoints. | L&D Admins, Instructional Designers |
| learning paths | Prerequisite Enforcement | Ensures required courses/skills are completed before unlocking downstream content. | Learners, L&D Admins |
| learning paths | Milestone Tracking | Tracks path progress by phase, milestone completion, and expected timeline adherence. | Learners, Managers, L&D Admins |
| learning paths | Role-Based Path Assignment | Auto-assigns paths by job role, department, location, or business unit rules. | L&D Admins, HR Admins |
| learning paths | Optional Elective Branching | Allows learners to choose electives within defined path branches while preserving core requirements. | Learners, L&D Admins |
| cohorts | Cohort Creation & Management | Organizes learners into time-bound groups by intake, role, or program for coordinated delivery. | L&D Admins, Program Managers |
| cohorts | Cohort Enrollment Rules | Assigns learners to cohorts through manual selection or dynamic rule criteria. | L&D Admins |
| cohorts | Cohort Calendar | Shares cohort-specific schedules, events, deadlines, and live-session timelines. | Learners, Instructors, Program Managers |
| cohorts | Group Progress Monitoring | Provides cohort-level dashboards for completion, risk, and engagement tracking. | Managers, Program Managers, L&D Admins |
| cohorts | Facilitator Communication Tools | Enables announcements and targeted messaging to members of specific cohorts. | Instructors, Program Managers |
| skills | Skills Taxonomy Management | Maintains enterprise skill framework with categories, proficiency levels, and relationships. | Talent Leaders, L&D Admins |
| skills | Skill Mapping to Content | Tags courses and assets to skills for targeted development and discovery. | Instructional Designers, L&D Admins |
| skills | Skill Assessments | Measures current proficiency through tests, observations, or manager validations. | Learners, Managers, Assessors |
| skills | Skill Gap Analysis | Compares required vs. demonstrated skills at individual/team/org levels. | Managers, Talent Leaders, L&D Admins |
| skills | Skill Development Recommendations | Recommends learning activities based on role needs, gaps, and career goals. | Learners, Managers |
| analytics | Executive Dashboards | Provides KPI dashboards for adoption, completion, compliance, and capability-building outcomes. | Executives, L&D Leaders |
| analytics | Learner Progress Reports | Delivers detailed progress and performance reporting by learner, team, or program. | Managers, L&D Admins |
| analytics | Content Effectiveness Analytics | Analyzes completion rates, assessment outcomes, and feedback to optimize content quality. | Instructional Designers, L&D Leaders |
| analytics | Compliance Reporting | Generates audit-ready reports on mandatory training completion and exceptions. | Compliance Admins, Auditors |
| analytics | Predictive Risk Alerts | Flags at-risk learners using inactivity, due-date risk, and performance indicators. | Managers, L&D Admins |
| analytics | Data Export & BI Connectors | Exposes governed exports/APIs/connectors for enterprise BI and data warehousing. | Data Analysts, IT Admins |
| enterprise administration | Multi-Tenant Management | Supports tenant isolation, tenant-level branding, policy control, and delegated administration. | SaaS Platform Admins, Enterprise Admins |
| enterprise administration | Organization Hierarchy Management | Models business units, regions, departments, and reporting structures for scoped administration. | Enterprise Admins, HR Admins |
| enterprise administration | Role-Based Access Control | Defines granular roles/permissions for learners, managers, instructors, and admins. | Enterprise Admins, Security Admins |
| enterprise administration | SSO & Identity Federation | Integrates SAML/OIDC identity providers with just-in-time provisioning and secure login. | IT Admins, Security Admins |
| enterprise administration | User Lifecycle Management | Automates onboarding, updates, deactivation, and reactivation of user accounts. | HR Admins, IT Admins |
| enterprise administration | Branding & White-Labeling | Customizes logos, themes, domains, and email templates per tenant/business unit. | Enterprise Admins, Marketing Ops |
| enterprise administration | Audit Logs | Records immutable admin/user/system activities for governance and troubleshooting. | Security Admins, Auditors |
| compliance | Mandatory Training Assignment | Assigns regulatory and policy training based on jurisdiction, role, and risk profile. | Compliance Admins, Managers |
| compliance | Policy Attestation Tracking | Captures learner acknowledgments for policies with timestamped attestations. | Learners, Compliance Admins |
| compliance | Regulation Mapping | Maps courses/certifications to regulatory controls and internal policies. | Compliance Admins, Risk Teams |
| compliance | Exception & Waiver Management | Handles documented exemptions, approvals, and compensating controls workflows. | Compliance Admins, Managers |
| compliance | Audit Evidence Repository | Stores completion records, attestations, and reports for inspection readiness. | Compliance Admins, Auditors |
| compliance | Compliance Escalation Workflows | Escalates overdue mandatory items to managers and compliance leadership. | Compliance Admins, Managers |
| integrations | HRIS Integration | Synchronizes worker profiles, org structures, and employment status from HR systlms. | HR Admins, IT Admins |
| integrations | CRM/ERP Integration | Exchanges training and certification data with operational enterprise systlms. | IT Admins, Business Ops |
| integrations | Webinar/Virtual Classroom Integration | Connects with meeting platforms for session launch, attendance, and recording ingestion. | Instructors, L&D Admins |
| integrations | Content Provider Integrations | Aggregates third-party content libraries and updates availability metadata. | L&D Admins, Learners |
| integrations | API & Webhook Framework | Provides secure APIs/webhooks for event-driven integration with enterprise ecosystlms. | IT Admins, Developers |
| integrations | Data Warehouse Integration | Schedules reliable data pipelines for analytics and enterprise reporting environments. | Data Engineers, BI Teams |
| mobile access | Native Mobile Apps | Delivers iOS/Android apps for training access, tracking, and notifications. | Learners, Managers |
| mobile access | Responsive Web Experience | Ensures browser-based LMS usability across tablets and smartphones. | Learners, Instructors |
| mobile access | Offline Learning Mode | Enables download and offline consumption with synchronized progress upon reconnect. | Field Employees, Learners |
| mobile access | Mobile Push Notifications | Sends due-date reminders, assignment alerts, and learning nudges to devices. | Learners, Managers |
| mobile access | Mobile Assessment Support | Supports quiz-taking and assignment workflows optimized for mobile devices. | Learners |
| mobile access | Mobile Security Controls | Enforces MDM policies, device restrictions, and secure app access controls. | IT Admins, Security Admins |
