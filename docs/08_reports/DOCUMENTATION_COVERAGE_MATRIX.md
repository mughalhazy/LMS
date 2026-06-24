# DOCUMENTATION_COVERAGE_MATRIX

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-21
Owner: AI

---

## Coverage Assessment

This matrix assesses documentation coverage across all major project dimensions.

Legend:
- ✅ COVERED — documented and verified from code
- ⚠️ PARTIAL — documented but with gaps or TBD sections
- ❌ MISSING — not documented
- 🔒 FROZEN — canonical; changes require owner approval

---

## Architecture Documentation

| Topic | Document | Status |
|---|---|---|
| Core system architecture | docs/architecture/core-system-architecture.md | ✅ |
| Domain-driven design map | docs/architecture/domain-driven-design-map.md | ✅ |
| Microservice boundary map | docs/architecture/microservice-boundary-map.md | ✅ |
| Multi-tenant isolation model | docs/architecture/multi-tenant-isolation-model.md | ✅ |
| Event-driven architecture | docs/architecture/event-driven-architecture.md | ✅ |
| API versioning strategy | docs/architecture/api-versioning-strategy.md | ✅ |
| Observability architecture | docs/architecture/observability-architecture.md | ✅ |
| **Two-layer architecture (services/ + backend/)** | **workspace/sessions/U10/** | ✅ (U10) |
| **Cross-layer dependency map** | **workspace/sessions/U10/U10_LMS_CROSS_LAYER_DEPENDENCY_MAP.md** | ✅ (U10) |
| **Reverse dependencies** | **workspace/sessions/U10/U10_LMS_RUNTIME_IMPORT_TRACE.md** | ✅ (U10) |
| Security architecture | docs/architecture/security-architecture.md | ✅ |
| Scalability strategy | docs/architecture/scalability-strategy.md | ✅ |
| Platform evolution model | docs/architecture/platform-evolution-model.md | ✅ |
| Deployment architecture | ❌ MISSING | ❌ |
| CI/CD pipeline | ❌ MISSING (none exists in Repo) | ❌ |

---

## Domain Model Documentation

| Domain | Design Doc | Spec Docs | Status |
|---|---|---|---|
| Identity | docs/designs/auth-rsa-key-design.md | docs/specs/auth-service-spec.md | ✅ |
| Organization | TBD | docs/specs/tenant-service-spec.md, org-hierarchy-spec.md | ⚠️ |
| Learning Structure | docs/designs/catalog-service-design.md | docs/specs/course-service-spec.md, lesson-service-spec.md | ✅ |
| Learning Runtime | docs/architecture/domain-driven-design-map.md | docs/specs/features/progress-tracking-spec.md | ⚠️ |
| Assessment | — | docs/specs/assessment-service-spec.md, exam-engine-spec.md | ✅ |
| Certification | docs/specs/GEN_14_certificate_service.md | — | ⚠️ |
| Analytics | docs/designs/analytics-intelligence-layer-design.md | docs/specs/analytics-service-spec.md | ✅ |
| AI | docs/designs/ai-tutor-assist-design.md, ai-learning-copilot.md | docs/specs/ai-tutor-service-spec.md | ⚠️ |
| **Commerce** | docs/designs/commerce-domain-architecture.md | ⚠️ 6 specs TBD (R-008) | ⚠️ |
| **Academy Ops (Pakistan)** | docs/designs/academy-operations-domain.md | ❌ No spec for academy-commerce-service | ❌ |
| Platform | docs/architecture/ (multiple) | Multiple specs | ✅ |

---

## Service Specification Coverage

### Backend Services With Confirmed Specs (docs/specs/)

| Service | Spec File |
|---|---|
| auth-service | docs/specs/auth-service-spec.md |
| analytics-service | docs/specs/analytics-service-spec.md |
| api-key-service | docs/specs/api-key-service-spec.md |
| assessment-service | docs/specs/assessment-service-spec.md |
| attempt-service | docs/specs/attempt-service-spec.md |
| badge-service | docs/specs/badge-service-spec.md |
| capability-registry | docs/specs/capability-registry-service-spec.md |
| catalog-service | docs/specs/catalog-service-spec.md (created U7) |
| certificate-service | docs/specs/GEN_14_certificate_service.md |
| cohort-service | docs/specs/cohort-service-spec.md |
| course-service | docs/specs/course-service-spec.md |
| department-service | docs/specs/department-service-spec.md |
| email-service | docs/specs/email-service-spec.md |
| enrollment-service | docs/specs/enrollment-service-spec.md |
| enterprise-control | docs/specs/enterprise-control-spec.md |
| event-ingestion | docs/specs/event-ingestion-spec.md |
| exam-engine | docs/specs/exam-engine-spec.md |
| financial-ledger | docs/specs/financial-ledger-spec.md |
| group-service | docs/specs/group-service-spec.md |
| hr-helpdesk | docs/specs/hr-helpdesk-service-spec.md |
| institution-service | docs/specs/institution-service-spec.md |
| integration-service | docs/specs/integration-service-spec.md |
| interaction-layer-service | docs/specs/interaction-layer-spec.md |
| learning-analytics | docs/specs/learning-analytics-service-spec.md |
| media-service | docs/specs/media-pipeline-spec.md |
| media-security | docs/specs/media-security-spec.md |
| notification-service | docs/specs/notification-service-spec.md |
| offline-sync-service | docs/specs/offline-sync-spec.md |
| onboarding | docs/specs/onboarding-spec.md |
| operations-os | docs/specs/operations-os-spec.md |
| program-service | docs/specs/program-service-spec.md |
| progress-service | docs/specs/progress-service-spec.md |
| push-service | docs/specs/push-service-spec.md |
| quiz-engine | docs/specs/quiz-engine-spec.md |
| rbac-service | docs/specs/rbac-service-spec.md |
| recommendation-service | docs/specs/recommendation-service-spec.md |
| session-service | docs/specs/session-service-spec.md |
| skill-inference | docs/specs/skill-inference-service-spec.md |
| sso-service | docs/specs/sso-spec.md |
| system-economics-service | docs/specs/system-economics-spec.md |
| tenant-service | docs/specs/tenant-service-spec.md |
| usage-metering | docs/specs/usage-metering-service-spec.md |
| user-service | docs/specs/user-service-spec.md |
| webhook-service | docs/specs/webhook-system-spec.md |
| workflow-engine | docs/specs/workflow-engine-spec.md |

**Specced: 45 of 69 backend services**

### Backend Services WITHOUT Canonical Specs (R-008 targets)

| Service | Status |
|---|---|
| academy-commerce-service | ❌ NO SPEC |
| ai-tutor-service | ❌ NO SPEC (design doc exists) |
| audit-policy-service | ❌ NO SPEC |
| checkout-service | ❌ NO SPEC (design doc exists) |
| config-service | ❌ NO SPEC (design doc exists) |
| content-service | ❌ NO SPEC (feature spec exists) |
| course-generation-service | ❌ NO SPEC (design doc: docs/designs/ai-course-generation-pipeline.md) |
| entitlement-service | ❌ NO SPEC (design doc exists) |
| feature-flag-service | ❌ NO SPEC (feature spec exists) |
| hris-sync-service | ❌ NO SPEC (integration doc exists) |
| invoice-billing-service | ❌ NO SPEC (design doc exists) |
| learning-path-service | ❌ NO SPEC (feature spec exists) |
| lesson-service | ❌ NO SPEC (feature spec exists) |
| lti-service | ❌ NO SPEC (integration docs exist) |
| org-service | ❌ NO SPEC (feature spec exists) |
| owner-economics-service | ❌ NO SPEC (design doc exists) |
| payment-service | ❌ NO SPEC (design doc exists) |
| prerequisite-engine-service | ❌ NO SPEC (feature spec exists) |
| reporting-service | ❌ NO SPEC (feature spec exists) |
| revenue-service | ❌ NO SPEC (design doc exists) |
| review-service | ❌ NO SPEC |
| scorm-service | ❌ NO SPEC (feature spec exists) |
| skill-analytics-service | ❌ NO SPEC (feature spec exists) |
| subscription-service | ❌ NO SPEC (design doc exists) |

**Unspecced: 24 of 69 backend services (35%)**

---

## Contract Documentation

| Contract | Document | Status |
|---|---|---|
| Capability gating | docs/contracts/capability-gating-model.md | ✅ |
| Capability interface | docs/contracts/capability-interface-contract.md | ✅ |
| Communication adapter | docs/contracts/communication-adapter-contract.md | ✅ |
| Config resolution | docs/contracts/config-resolution-interface-contract.md | ✅ |
| Content storage | docs/contracts/content-storage-model.md | ✅ |
| Entitlement interface | docs/contracts/entitlement-interface-contract.md | ✅ |
| Media security | docs/contracts/media-security-interface-contract.md | ✅ |
| Offline sync | docs/contracts/offline-sync-interface-contract.md | ✅ |
| Payment provider adapter | docs/contracts/payment-provider-adapter-contract.md | ✅ |
| Storage adapter | docs/contracts/storage-adapter-interface-contract.md | ✅ |
| Usage metering | docs/contracts/usage-metering-interface-contract.md | ✅ |
| **Checkout/Order contract** | ❌ MISSING | ❌ |
| **Academy Ops contract** | ❌ MISSING | ❌ |
| **System of Record contract** | ❌ MISSING | ❌ |

---

## Test Coverage

| Area | Test Files | Status |
|---|---|---|
| Backend services | 78 files in backend/services/ | ⚠️ PARTIAL (not all services have tests) |
| Domain services (services/) | 27 files in services/ | ⚠️ PARTIAL |
| Frontend | 0 files | ❌ ZERO TESTS |
| Integration tests (cross-service) | TBD – REQUIRES VERIFICATION | ❌ UNKNOWN |
| Load tests | Planned (U9 LOAD_TEST_PLAN.md) | ❌ NOT YET |
| Security tests | Planned (U9 SECURITY_TEST_PLAN.md) | ❌ NOT YET |
| Contract tests | Planned (U9 TEST_SUITE_PLAN.md P3) | ❌ NOT YET |

---

## Deployment Documentation

| Topic | Status |
|---|---|
| Dockerfiles | ❌ NONE IN REPO |
| CI/CD pipeline | ❌ NONE IN REPO |
| Environment variables | ❌ NOT DOCUMENTED |
| Class-based service startup | ❌ NOT DOCUMENTED (owner decision D-002) |
| Scaling strategy | docs/architecture/scalability-strategy.md | ✅ |
| Deployment target | ❌ NOT DOCUMENTED (owner decision D-003) |

---

## Coverage Summary

| Dimension | Coverage | Status |
|---|---|---|
| Architecture | ~85% | ⚠️ Missing deployment architecture |
| Domain model | ~80% | ⚠️ Commerce/Academy Ops gaps |
| Service specs | 65% (45/69) | ⚠️ 24 unspecced |
| Interface contracts | ~80% | ⚠️ 3 contracts missing |
| Tests | 30% (105 files) | ❌ No frontend, no integration, no load |
| Deployment | 5% | ❌ No Dockerfiles, no CI/CD |
| Governance (NEW) | 100% | ✅ Phase 1 complete |
