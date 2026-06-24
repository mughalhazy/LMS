# SERVICE_CATALOG

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Complete catalog of all registered backend services. Authoritative source: `infrastructure/deployment/service-manifest.json` (v1). **Do not manually update this catalog without updating the manifest first.**

Total services: **69** *(corrected from 65 — pre-frontend delta audit 2026-06-23)*

---

## Service Summary by Type

| Type | Count | Description |
|---|---|---|
| Python FastAPI (`app.main:app`) | 63 | Standard FastAPI microservices |
| Python non-standard (`api:app`) | 1 | payment-service |
| Node.js (`npm run start`) | 2 | prerequisite-engine-service, scorm-service |
| Class-based (`service:ClassName`) | 3 | capability-registry, config-service, entitlement-service (in root `services/`) — no runtime found (see OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md OA-004) |

---

## Full Service Registry

Sorted by port number. Source: `infrastructure/deployment/service-manifest.json`.

| Port | Service Name | Runtime | App Module | Path | Domain |
|---|---|---|---|---|---|
| 8100 | ai-tutor-service | python | app.main:app | backend/services/ai-tutor-service | AI / Learning |
| 8101 | api-key-service | python | app.main:app | backend/services/api-key-service | Auth / Platform |
| 8102 | assessment-service | python | app.main:app | backend/services/assessment-service | Assessment |
| 8103 | attempt-service | python | app.main:app | backend/services/attempt-service | Assessment |
| 8104 | auth-service | python | app.main:app | backend/services/auth-service | Auth |
| 8105 | badge-service | python | app.main:app | backend/services/badge-service | Gamification |
| 8106 | certificate-service | python | app.main:app | backend/services/certificate-service | Certification |
| 8107 | cohort-service | python | app.main:app | backend/services/cohort-service | Learning |
| 8108 | content-service | python | app.main:app | backend/services/content-service | Content |
| 8109 | course-generation-service | python | app.main:app | backend/services/course-generation-service | AI / Content |
| 8110 | course-service | python | app.main:app | backend/services/course-service | Content |
| 8111 | department-service | python | app.main:app | backend/services/department-service | Organization |
| 8112 | email-service | python | app.main:app | backend/services/email-service | Communication |
| 8113 | enrollment-service | python | app.main:app | backend/services/enrollment-service | Learning |
| 8114 | event-ingestion-service | python | app.main:app | backend/services/event-ingestion-service | Analytics |
| 8115 | group-service | python | app.main:app | backend/services/group-service | Organization |
| 8116 | hris-sync-service | python | app.main:app | backend/services/hris-sync-service | Organization |
| 8117 | learning-analytics-service | python | app.main:app | backend/services/learning-analytics-service | Analytics |
| 8118 | learning-path-service | python | app.main:app | backend/services/learning-path-service | Learning |
| 8119 | lesson-service | python | app.main:app | backend/services/lesson-service | Content |
| 8120 | lti-service | python | app.main:app | backend/services/lti-service | Integration |
| 8121 | media-service | python | app.main:app | backend/services/media-service | Content |
| 8122 | notification-service | python | app.main:app | backend/services/notification-service | Communication |
| 8123 | org-service | python | app.main:app | backend/services/org-service | Organization |
| 8124 | prerequisite-engine-service | node | npm run start | backend/services/prerequisite-engine-service | Learning |
| 8125 | progress-service | python | app.main:app | backend/services/progress-service | Learning |
| 8126 | push-service | python | app.main:app | backend/services/push-service | Communication |
| 8127 | quiz-engine | python | app.main:app | backend/services/quiz-engine | Assessment |
| 8128 | rbac-service | python | app.main:app | backend/services/rbac-service | Auth / Platform |
| 8129 | recommendation-service | python | app.main:app | backend/services/recommendation-service | AI / Learning |
| 8130 | reporting-service | python | app.main:app | backend/services/reporting-service | Analytics |
| 8131 | scorm-service | node | npm run start | backend/services/scorm-service | Content / Integration |
| 8132 | skill-analytics-service | python | app.main:app | backend/services/skill-analytics-service | Analytics |
| 8133 | skill-inference-service | python | app.main:app | backend/services/skill-inference-service | AI / Learning |
| 8134 | sso-service | python | app.main:app | backend/services/sso-service | Auth |
| 8135 | tenant-service | python | app.main:app | backend/services/tenant-service | Platform |
| 8136 | user-service | python | app.main:app | backend/services/user-service | Platform |
| 8137 | webhook-service | python | app.main:app | backend/services/webhook-service | Integration |
| 8138 | program-service | python | app.main:app | backend/services/program-service | Learning |
| 8140 | capability-registry | python | service:CapabilityRegistryService | services/capability-registry | Platform (root layer) |
| 8141 | config-service | python | service:ConfigService | services/config-service | Platform (root layer) |
| 8142 | entitlement-service | python | service:EntitlementService | services/entitlement-service | Platform (root layer) |
| 8143 | academy-commerce-service | python | app.main:app | backend/services/academy-commerce-service | Commerce |
| 8144 | analytics-service | python | app.main:app | backend/services/analytics-service | Analytics |
| 8145 | audit-policy-service | python | app.main:app | backend/services/audit-policy-service | Platform / Compliance |
| 8146 | catalog-service | python | app.main:app | backend/services/catalog-service | Commerce |
| 8147 | checkout-service | python | app.main:app | backend/services/checkout-service | Commerce |
| 8148 | enterprise-control-service | python | app.main:app | backend/services/enterprise-control-service | Organization |
| 8149 | exam-engine | python | app.main:app | backend/services/exam-engine | Assessment |
| 8150 | feature-flag-service | python | app.main:app | backend/services/feature-flag-service | Platform |
| 8151 | financial-ledger-service | python | app.main:app | backend/services/financial-ledger-service | Commerce / Finance |
| 8152 | hr-helpdesk-service | python | app.main:app | backend/services/hr-helpdesk-service | Organization |
| 8153 | institution-service | python | app.main:app | backend/services/institution-service | Organization |
| 8154 | integration-service | python | app.main:app | backend/services/integration-service | Integration |
| 8155 | interaction-layer-service | python | app.main:app | backend/services/interaction-layer-service | Learning |
| 8156 | invoice-billing-service | python | app.main:app | backend/services/invoice-billing-service | Commerce / Finance |
| 8157 | media-security-service | python | app.main:app | backend/services/media-security-service | Content |
| 8158 | offline-sync-service | python | app.main:app | backend/services/offline-sync-service | Platform |
| 8159 | onboarding-service | python | app.main:app | backend/services/onboarding-service | Platform |
| 8160 | operations-os-service | python | app.main:app | backend/services/operations-os-service | Operations |
| 8161 | owner-economics-service | python | app.main:app | backend/services/owner-economics-service | Commerce / Operations |
| 8162 | payment-service | python | api:app | backend/services/payment-service | Commerce / Finance |
| 8163 | revenue-service | python | app.main:app | backend/services/revenue-service | Commerce / Finance |
| 8164 | review-service | python | app.main:app | backend/services/review-service | Learning |
| 8165 | session-service | python | app.main:app | backend/services/session-service | Learning |
| 8166 | subscription-service | python | app.main:app | backend/services/subscription-service | Commerce |
| 8167 | system-economics-service | python | app.main:app | backend/services/system-economics-service | Commerce / Operations |
| 8168 | usage-metering-service | python | app.main:app | backend/services/usage-metering-service | Platform |
| 8169 | workflow-engine | python | app.main:app | backend/services/workflow-engine | Platform |

---

## Service Groups by Domain

### Auth & Identity

| Service | Port | Notes |
|---|---|---|
| auth-service | 8104 | JWT issuance, session mgmt, password reset, SSO initiation; uses stdlib http.server |
| rbac-service | 8128 | Roles, permissions, authorization decisions |
| sso-service | 8134 | SSO callback and SAML/OIDC flows |
| api-key-service | 8101 | Programmatic API key management |

### Tenant & Platform

| Service | Port | Notes |
|---|---|---|
| tenant-service | 8135 | Tenant lifecycle, configuration, isolation enforcement |
| capability-registry | 8140 | Class-based; in root services/ layer |
| config-service | 8141 | Class-based; in root services/ layer |
| entitlement-service | 8142 | Class-based; in root services/ layer |
| feature-flag-service | 8150 | Feature flag management |
| audit-policy-service | 8145 | Audit log policy |
| usage-metering-service | 8168 | Usage tracking |
| onboarding-service | 8159 | Tenant/user onboarding flows |
| offline-sync-service | 8158 | Offline-capable sync |
| workflow-engine | 8169 | Workflow orchestration |

### Learning & Content

| Service | Port | Notes |
|---|---|---|
| enrollment-service | 8113 | Enrollment lifecycle, bulk assign |
| progress-service | 8125 | Lesson and course progress tracking |
| learning-path-service | 8118 | Learning path assignment |
| lesson-service | 8119 | Lesson management |
| course-service | 8110 | Course management |
| content-service | 8108 | Content management |
| cohort-service | 8107 | Cohort management |
| program-service | 8138 | Program management |
| session-service | 8165 | Learning session management |
| interaction-layer-service | 8155 | Learner interaction |
| review-service | 8164 | Reviews and ratings |
| certificate-service | 8106 | Certificate issuance |
| badge-service | 8105 | Badge gamification |

### Assessment

| Service | Port | Notes |
|---|---|---|
| assessment-service | 8102 | Assessment management |
| attempt-service | 8103 | Assessment attempt tracking |
| quiz-engine | 8127 | Quiz delivery |
| exam-engine | 8149 | Exam engine |

### Media

| Service | Port | Notes |
|---|---|---|
| media-service | 8121 | Media upload and management |
| media-security-service | 8157 | Signed URL / media access control |
| scorm-service | 8131 | SCORM runtime (Node.js) |

### Analytics & AI

| Service | Port | Notes |
|---|---|---|
| analytics-service | 8144 | Analytics queries |
| event-ingestion-service | 8114 | Event collection |
| learning-analytics-service | 8117 | Learning-specific analytics |
| skill-analytics-service | 8132 | Skill analytics |
| skill-inference-service | 8133 | Skill inference (AI) |
| recommendation-service | 8129 | Content recommendations (AI) |
| ai-tutor-service | 8100 | AI tutoring |
| course-generation-service | 8109 | AI course generation |
| reporting-service | 8130 | Reports |

### Commerce & Finance

| Service | Port | Notes |
|---|---|---|
| checkout-service | 8147 | Checkout sessions and orders; uses stdlib http.server |
| payment-service | 8162 | Payment processing; uses `api:app` (not app.main:app) |
| invoice-billing-service | 8156 | Invoicing |
| financial-ledger-service | 8151 | Financial ledger |
| subscription-service | 8166 | Subscription lifecycle |
| catalog-service | 8146 | Product catalog |
| revenue-service | 8163 | Revenue tracking |
| academy-commerce-service | 8143 | Academy-specific commerce |
| owner-economics-service | 8161 | Owner economics |
| system-economics-service | 8167 | Platform economics |

### Organization & HR

| Service | Port | Notes |
|---|---|---|
| user-service | 8136 | User profile management |
| org-service | 8123 | Organizational hierarchy |
| department-service | 8111 | Department management |
| group-service | 8115 | Group management |
| institution-service | 8153 | Institution/school management |
| enterprise-control-service | 8148 | Enterprise control plane |
| hris-sync-service | 8116 | HRIS data synchronization |
| hr-helpdesk-service | 8152 | HR helpdesk |

### Communication

| Service | Port | Notes |
|---|---|---|
| notification-service | 8122 | Notifications |
| email-service | 8112 | Email delivery |
| push-service | 8126 | Push notifications |

### Integration

| Service | Port | Notes |
|---|---|---|
| integration-service | 8154 | Generic integration management |
| lti-service | 8120 | LTI 1.3 integration |
| webhook-service | 8137 | Outbound webhooks |
| prerequisite-engine-service | 8124 | Node.js prerequisite engine |

### Operations

| Service | Port | Notes |
|---|---|---|
| operations-os-service | 8160 | Operations dashboard |

---

## Non-Standard Services

### Services Not Using `app.main:app`

| Service | Port | Module | Notes |
|---|---|---|---|
| payment-service | 8162 | `api:app` | Non-standard entrypoint; likely uses `api.py` instead of `app/main.py` |
| capability-registry | 8140 | `service:CapabilityRegistryService` | Class-based; in root `services/` layer; startup mechanism unconfirmed |
| config-service | 8141 | `service:ConfigService` | Class-based; in root `services/` layer; startup mechanism unconfirmed |
| entitlement-service | 8142 | `service:EntitlementService` | Class-based; in root `services/` layer; startup mechanism unconfirmed |
| prerequisite-engine-service | 8124 | N/A | Node.js; `npm run start` |
| scorm-service | 8131 | N/A | Node.js; `npm run start` |

Note: `auth-service` is registered as `app.main:app` in the manifest but its implementation uses Python's stdlib `http.server`, not FastAPI. The `app.main:app` reference may be a manifest entry for a FastAPI wrapper, or the manifest entry may be stale.

---

## Services With Engineering Specs

The following services have specs in `docs/specs/`:

auth-service, assessment-service, certificate-service, cohort-service, course-service, enrollment-service, progress-service, tenant-service, rbac-service, notification-service, catalog-service, session-service, user-service, ai-tutor-service, recommendation-service, skill-inference-service, learning-analytics-service, analytics-service, capability-registry (capability-registry-service-spec.md), badge-service, attempt-service, department-service, email-service, group-service, push-service, quiz-engine, hr-helpdesk-service, sso-service, program-service, and others.

See `docs/specs/` for individual spec files (73 files total).

---

## Related Documents

- `infrastructure/deployment/service-manifest.json` — authoritative registry
- `docs/01_backend/BACKEND_ARCHITECTURE.md` — architecture overview
- `docs/01_backend/API_CONTRACT.md` — API patterns
- `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` — capture summary
