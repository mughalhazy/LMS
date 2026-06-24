# FEATURE_SCOPE

Status: Active
Authority Level: High
Last Reviewed: 2026-06-21
Owner: Shared

---

## Source Authority

Extracted from: docs/specs/, docs/designs/, service-manifest.json, docs/architecture/domain-driven-design-map.md, docs/market/

---

## 1. Core Platform Features (Confirmed in Codebase)

These features have confirmed implementation evidence (service exists in service-manifest.json + code in backend/services/).

### 1.1 Identity and Access
| Feature | Service | Evidence |
|---|---|---|
| User registration and login | auth-service | backend/services/auth-service/ |
| JWT RS256 authentication | auth-service | docs/designs/auth-rsa-key-design.md |
| Role-based access control (RBAC) | rbac-service | backend/services/rbac-service/ + spec |
| Single Sign-On (SSO) | sso-service | backend/services/sso-service/ |
| API key management | api-key-service | backend/services/api-key-service/ |
| Session management | session-service | backend/services/session-service/ |

### 1.2 Organization and Tenancy
| Feature | Service | Evidence |
|---|---|---|
| Multi-tenant isolation | tenant-service | backend/services/tenant-service/ + docs/architecture/multi-tenant-isolation-model.md |
| Organization hierarchy | org-service, institution-service | backend/services/ |
| Department management | department-service | backend/services/department-service/ |
| Group and cohort management | group-service, cohort-service | backend/services/ |

### 1.3 Learning Structure
| Feature | Service | Evidence |
|---|---|---|
| Course creation and management | course-service | backend/services/course-service/ + spec |
| Lesson management | lesson-service | backend/services/lesson-service/ + spec |
| Content management | content-service | backend/services/content-service/ |
| Program/pathway management | program-service, learning-path-service | backend/services/ |
| Course reviews and ratings | review-service | backend/services/review-service/ + app/models.py (Review: rating 1-5, pending/published/rejected lifecycle) |
| SCORM runtime | scorm-service (Node.js) | backend/services/scorm-service/ |
| Prerequisite engine | prerequisite-engine-service (Node.js) | backend/services/prerequisite-engine-service/ |

### 1.4 Learning Runtime
| Feature | Service | Evidence |
|---|---|---|
| Enrollment | enrollment-service | backend/services/enrollment-service/ + spec (v2 API) |
| Progress tracking | progress-service | backend/services/progress-service/src/entities.py |
| Learning session | session-service | backend/services/session-service/ |
| Offline sync | offline-sync-service | backend/services/offline-sync-service/ + services/offline-sync/ |

### 1.5 Assessment and Certification
| Feature | Service | Evidence |
|---|---|---|
| Assessment creation and delivery | assessment-service | backend/services/assessment-service/ + spec |
| Attempt tracking and scoring | attempt-service | backend/services/attempt-service/ |
| Exam engine | exam-engine | backend/services/exam-engine/ + services/exam-engine/ |
| Quiz engine | quiz-engine | backend/services/quiz-engine/ |
| Certificate issuance | certificate-service | backend/services/certificate-service/ + spec |
| Badge issuance | badge-service | backend/services/badge-service/ |

### 1.6 Commerce and Billing
| Feature | Service / Component | Evidence |
|---|---|---|
| Checkout (JazzCash/EasyPaisa) | checkout-service / services/commerce/checkout.py | backend/services/checkout-service/ + .pyc in services/commerce/ |
| Payment processing | payment-service + integrations/payments/ | integrations/payments/orchestration.py |
| Invoice and billing | invoice-billing-service / services/commerce/billing.py | backend/services/invoice-billing-service/ |
| Subscription management | subscription-service | backend/services/subscription-service/ (HS256 — debt tracked) |
| Revenue analytics | revenue-service | backend/services/revenue-service/ |
| Owner/teacher economics | owner-economics-service | backend/services/owner-economics-service/ |
| Academy commerce (Pakistan) | academy-commerce-service | backend/services/academy-commerce-service/ |
| Capability gating | entitlement-service | services/entitlement-service/ (DEPLOYED) |

### 1.7 Academy Operations (Pakistan-specific)
| Feature | Component | Evidence |
|---|---|---|
| Branch management | services/academy-ops/ | services/academy-ops/service.py:_domain_owner |
| Batch management | services/academy-ops/ | 1357-line orchestrator |
| Timetable scheduling | services/academy-ops/ | Conflict detection logic |
| Attendance tracking | services/academy-ops/ → system-of-record | SOR.record_attendance() |
| Fee tracking | services/academy-ops/ → system-of-record | SOR.post_invoice_to_ledger() |
| Teacher assignment | services/academy-ops/ | TeacherBatchEconomics model |
| Student system of record | services/system-of-record/ | Enrollment/invoice/attendance ledger |

### 1.8 Notifications and Communication
| Feature | Service | Evidence |
|---|---|---|
| Notification dispatch | notification-service | backend/services/notification-service/ (HS256 — debt tracked) |
| WhatsApp / SMS / Email | services/notification-service/orchestration.py | integrations/communication/ |
| Push notifications | push-service | backend/services/push-service/ |
| Email service | email-service | backend/services/email-service/ |

### 1.9 Analytics and Reporting
| Feature | Service | Evidence |
|---|---|---|
| Learning analytics | learning-analytics-service | backend/services/learning-analytics-service/ + spec |
| Analytics service | analytics-service | backend/services/analytics-service/ |
| Reporting | reporting-service | backend/services/reporting-service/ |
| Skill analytics | skill-analytics-service | backend/services/skill-analytics-service/ |

### 1.10 AI Features
| Feature | Service | Evidence |
|---|---|---|
| AI tutor | ai-tutor-service | backend/services/ai-tutor-service/ |
| Recommendation engine | recommendation-service | backend/services/recommendation-service/ |
| Skill inference | skill-inference-service | backend/services/skill-inference-service/ |
| Course generation (AI) | course-generation-service | backend/services/course-generation-service/ + docs/designs/ai-course-generation-pipeline.md |
| Adaptive learning | FGAP-002 — design doc exists, no service in manifest, deferred (not permanent exclusion) | docs/designs/adaptive-learning-engine.md |

### 1.11 Platform Infrastructure
| Feature | Service | Evidence |
|---|---|---|
| Event ingestion | event-ingestion-service | backend/services/event-ingestion-service/ |
| Webhook system | webhook-service | backend/services/webhook-service/ + spec |
| Feature flags | feature-flag-service | backend/services/feature-flag-service/ |
| Usage metering | usage-metering-service | backend/services/usage-metering-service/ |
| HRIS sync | hris-sync-service | backend/services/hris-sync-service/ + integrations/hris-sync-spec.md |
| LTI (consumer + provider) | lti-service | backend/services/lti-service/ + docs/integrations/lti-consumer-spec.md |
| Media management | media-service, media-security-service | backend/services/ |
| Financial ledger | financial-ledger-service | backend/services/financial-ledger-service/ |
| HR helpdesk | hr-helpdesk-service | backend/services/hr-helpdesk-service/ |
| System economics | system-economics-service | backend/services/system-economics-service/ |
| Audit policy | audit-policy-service | backend/services/audit-policy-service/ |

---

## 2. Features In Design (Not Yet Fully Implemented)

These have design documents but their implementation status requires verification.

| Feature | Design Document | Status |
|---|---|---|
| Adaptive learning engine | docs/designs/adaptive-learning-engine.md | FGAP-002: No service in manifest. Design doc exists. Deferred to adaptive learning sprint. Not permanent exclusion. |
| AI learning copilot | docs/designs/ai-learning-copilot.md | FGAP-003: Confirmed services (ai-tutor, recommendation, course-gen) in scope now. Full copilot overlay deferred to AI sprint. |
| Vocational training domain | docs/specs/vocational-training-domain-spec.md | Deferred (MO-042) |
| Teacher marketplace | Deferred | (MO-043) |
| Offline box | Deferred | (MO-044) |
| Urdu i18n | Deferred | (MO-041) |
| Learner risk insights | docs/designs/learner-risk-insights-design.md | FGAP-004: No service in manifest. Design doc exists. Deferred to risk insights sprint. |

---

## 3. Feature Scope Boundaries

### In Scope (Current Phase)
- Pakistan academy operations (branches, batches, timetable, attendance, fees)
- JazzCash/EasyPaisa payment processing
- Core learning lifecycle (enrollment → progress → certificate)
- Multi-tenant SaaS (tenant isolation, config hierarchy)
- RBAC and identity
- Event-driven architecture (39 topics)

### Out of Scope (Current Phase)
- Urdu i18n (MO-041)
- Vocational service (MO-042)
- Teacher marketplace (MO-043)
- Offline box (MO-044)
- Multi-country payment (only PK currently at domain layer)
- Adaptive learning engine (design only)
- Global education model (docs/designs/global-education-model-framework.md — design only)

---

## 4. Capability Registry Reference

**Source of truth for all platform capabilities:** `docs/architecture/capabilities/` (B0P05–B0P08 JSON files)

- B0P05: Business capabilities
- B0P06: Communication capabilities
- B0P07: Delivery capabilities
- B0P08: Intelligence capabilities

Also: `docs/specs/B0P04_core_capabilities.json`
