# DOC_02 Product Capabilities Matrix — Enterprise LMS V2

This matrix defines capability ownership and dependencies across tiered modules for Enterprise LMS V2. Capabilities are aligned to core repo entities: `User`, `Course`, `Lesson`, `Enrollment`, `Progress`, and `Certificate`.

## Capability Matrix

| Capability | Domain | Responsible Service | Dependencies | Capability Gate (Yes/No) |
|---|---|---|---|---|
| User Identity & Access Lifecycle | Core LMS | `auth_identity_service` + `user_profile_service` | `tenant_context_service`, `organization_catalog_service`; entity dependency: **User** | No |
| Course Catalog & Discovery | Core LMS | `course_catalog_service` | `user_profile_service` (audience targeting), `organization_catalog_service`; entity dependency: **Course** | No |
| Lesson Authoring & Publish Workflow | Core LMS | `content_delivery_service` + `course_catalog_service` | `course_service_spec` lifecycle (`create_course`, `publish_course`), lesson lifecycle APIs; entity dependency: **Lesson**, **Course** | No |
| Enrollment Orchestration | Core LMS | `enrollment_service` | `user_profile_service`, `course_catalog_service`, `learning_path_service`; entity dependency: **Enrollment**, **User**, **Course** | No |
| Progress Tracking & Completion State | Core LMS | `progress_tracking_service` | `enrollment_service`, lesson completion events, `assessment_service`; entity dependency: **Progress**, **Lesson**, **Enrollment** | No |
| Certificate Issuance & Expiry | Core LMS | `certification_service` | `progress_tracking_service` (`CourseCompletionTracked`), policy rules, `notification_service`; entity dependency: **Certificate**, **Progress** | No |
| Academy Path Programs | Academy Module | `learning_path_service` | `course_catalog_service`, `enrollment_service`, `progress_tracking_service`; entity dependency: **Course**, **Enrollment**, **Progress** | Yes |
| Cohort-Based Academy Enrollment Controls | Academy Module | `enrollment_service` + `organization_catalog_service` | team/cohort mappings, approval flows, due-date policies; entity dependency: **User**, **Enrollment** | Yes |
| AI Learning Recommendations | AI Module | `recommendation-service` | `progress_tracking_service`, `user_profile_service`, `course_catalog_service`, `learning_analytics` features; entity dependency: **User**, **Course**, **Progress** | Yes |
| AI Course & Lesson Draft Generation | AI Module | `ai_course_generation` pipeline with `course_catalog_service` | prerequisite graph, pedagogical template, content sources, human review workflow; entity dependency: **Course**, **Lesson** | Yes |
| Predictive Risk & Drop-off Analytics | Analytics Module | `reporting_analytics_service` | event ingestion, `progress_tracking_service`, `enrollment_service`; entity dependency: **Progress**, **Enrollment**, **Course** | Yes |
| Learner/Manager Progress Reporting | Analytics Module | `reporting_analytics_service` + `manager-dashboard-service` | KPI aggregates, dashboard feeds, team hierarchy, `notification_service`; entity dependency: **Progress**, **User**, **Course** | Yes |
| Tenant & Plan Capability Management | Enterprise Module | `tenant_context_service` + `config_feature_flag_service` | `tenant_service`, entitlement policy, runtime feature flags; entity dependency: **User** (tenant admins) | No |
| Enterprise Compliance & Evidence Reporting | Enterprise Module | `reporting_analytics_service` + `compliance-reporting-service` | `certification_service`, audit logs, policy attestation records; entity dependency: **Certificate**, **Progress**, **User** | Yes |
| Multi-tenant Branding & Delegated Administration | Enterprise Module | `tenant_service` + `organization_catalog_service` | RBAC, SSO federation, tenant configuration baseline; entity dependency: **User** | Yes |

## Capability Tier Coverage Map

- **Core LMS:** foundational learning operations for `User`, `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`.
- **Academy Module:** structured programs and cohorts layered on top of core enrollment/progress.
- **AI Module:** recommendation and generation capabilities using learner/course/progress signals.
- **Analytics Module:** operational and predictive insights for managers and executives.
- **Enterprise Module:** tenant controls, governance, and enterprise-scale administration.

---

## QC LOOP

### QC Iteration 1 (Initial Evaluation)

| Category | Score (1–10) | Weakness Identified |
|---|---:|---|
| Capability coverage | 9 | Enterprise governance was present, but explicit delegated admin capability was under-specified. |
| Service ownership clarity | 9 | Some rows used domain-level naming without explicit service pairing for enterprise admin. |
| Compatibility with capability gating | 10 | Gating aligns to tenant-scoped flags and entitlement patterns. |
| Enterprise scalability | 9 | Needed explicit multi-tenant branding/delegated administration for large organizations. |

**Correction Applied:**
- Added **Multi-tenant Branding & Delegated Administration** capability under Enterprise Module with explicit service ownership (`tenant_service` + `organization_catalog_service`) and dependencies.
- Clarified service pairings for enterprise-facing capabilities.

### QC Iteration 2 (Post-Correction Re-evaluation)

| Category | Score (1–10) | Result |
|---|---:|---|
| Capability coverage | 10 | All requested entities and all five capability tiers are fully represented. |
| Service ownership clarity | 10 | Every row maps to concrete responsible services. |
| Compatibility with capability gating | 10 | Gated capabilities are tenant-plan/feature-flag compatible; core baseline remains ungated. |
| Enterprise scalability | 10 | Multi-tenant controls, compliance reporting, and delegated admin are explicitly included. |

**QC Status:** ✅ All categories are **10/10**.
