# DOMAIN_MODEL

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-21
Owner: Shared

---

## Source Authority

This document extracts from:
- `docs/architecture/domain-driven-design-map.md` (ARCH_03)
- `docs/anchors/tenant-contract.md`
- `docs/anchors/capability-resolution.md`
- `docs/architecture/core-system-architecture.md`
- `Repo/services/academy-ops/service.py` (domain_owner mapping — U10)

---

## 1. Bounded Context Map

| Domain | Mission | Key Services |
|---|---|---|
| **Identity** | User authentication, session, RBAC | auth-service, rbac-service, user-service, sso-service |
| **Organization** | Tenant/org/dept/team hierarchy | tenant-service, org-service, department-service, group-service, institution-service, onboarding-service |
| **Learning Structure** | Author and version learning artifacts | course-service, lesson-service, content-service, program-service, learning-path-service |
| **Learning Runtime** | Execute learning participation and completion | enrollment-service, progress-service, session-service, scorm-service, review-service |
| **Assessment** | Evaluate performance | assessment-service, attempt-service, exam-engine, quiz-engine |
| **Certification** | Issue, revoke, verify credentials | certificate-service, badge-service |
| **Analytics** | Reporting, projections, insights | analytics-service, learning-analytics-service, reporting-service, skill-analytics-service |
| **AI** | Tutoring, recommendation, generation | ai-tutor-service, recommendation-service, course-generation-service, skill-inference-service |
| **Commerce** | Billing, checkout, subscriptions, payments | commerce (services/), checkout-service, payment-service, invoice-billing-service, subscription-service, revenue-service, owner-economics-service, academy-commerce-service |
| **Academy Ops** | Branch/batch/timetable/attendance/fee management | academy-ops (services/), enterprise-control-service |
| **Platform** | Cross-cutting: notifications, events, integration, webhooks | notification-service, event-ingestion-service, integration-service, webhook-service, push-service, email-service, feature-flag-service, api-key-service, usage-metering-service |

---

## 2. Core Runtime Entities (Rails Heritage — Frozen)

These entities are the authoritative execution anchors. They must not be renamed or removed. "Rails heritage" refers to the original Rails LMS runtime (Enterprise LMS V2) whose core entities pre-date the Python microservices layer — they are retained in the Python migration as frozen aggregate roots.

| Entity | Service Owner | Evidence |
|---|---|---|
| User | user-service / auth-service | backend/services/user-service/ + auth-service/ |
| Course | course-service | backend/services/course-service/migrations/0001_create_courses.sql |
| Lesson | lesson-service | backend/services/lesson-service/migrations/0001_create_lessons.sql |
| Enrollment | enrollment-service | backend/services/enrollment-service/migrations/0001_create_enrollments.sql |
| Progress | progress-service | backend/services/progress-service/src/entities.py |
| Certificate | certificate-service | backend/services/certificate-service/ |

---

## 3. Canonical Tenant Model

Source: `docs/anchors/tenant-contract.md`

```json
{
  "tenant_id": "string (UUID, immutable)",
  "name": "string",
  "country_code": "string (ISO 3166-1 alpha-2, uppercase)",
  "segment_type": "string (controlled vocabulary)",
  "plan_type": "string (controlled plan key)",
  "addon_flags": ["string"]
}
```

**Rules:**
- `tenant_id` is mandatory and immutable
- `country_code` must be ISO 3166-1 alpha-2 uppercase
- `plan_type`, `segment_type`, `addon_flags` are declaration inputs — NOT decision outputs
- Resolved capabilities are NOT stored in the tenant contract
- Cross-service consumers must not infer capabilities from tenant records

---

## 4. Capability Resolution Model

Source: `docs/anchors/capability-resolution.md`

**Fixed sequence (mandatory):**
```
capability (definition) → config (overrides) → entitlement (decision) → final_state
```

**Config hierarchy:**
```
global → country → segment → tenant (4 levels; plan_type is evaluated by entitlement service — not a config resolution layer; runtime_override is not implemented)
```

**Ownership:**
| Concern | Owner |
|---|---|
| Capability definition | Capability Registry (services/capability-registry/) |
| Config override resolution | Config Service (services/config-service/) |
| Allow/deny decision | Entitlement Service (services/entitlement-service/) |
| Final state assembly | Calling service / API handler (the service initiating the check — never registry/config/entitlement internals) |

**MS-CONFIG-01 constraint:** Country/segment discriminators are opaque lookup keys. Services MUST NOT branch on them in business logic. Behavioral variation is entirely expressed through config values.

---

## 5. Domain Aggregates

Source: `docs/architecture/domain-driven-design-map.md` (ARCH_03)

### Identity Domain
- **User** (aggregate root) — UserAccount, UserProfile, SessionToken, RoleGrant
- **CredentialProfile** (aggregate root) — owned by auth-service (authentication factors, verification state)
- **RoleAssignment** (aggregate root)

### Organization Domain
- **Organization** (aggregate root) — OrganizationNode, DepartmentNode
- **Department** (aggregate root)
- **Team** (aggregate root)
- **Membership** (aggregate root)

### Learning Structure Domain
- **Course** ✅ (preserved aggregate root)
- **Lesson** ✅ (preserved aggregate root)
- **Program** (aggregate root)
- **LearningPath** (aggregate root)
- **ContentBlock** (entity)

### Learning Runtime Domain
- **Enrollment** ✅ (preserved aggregate root)
- **Progress** ✅ (preserved aggregate root)
- **LearnerSession** (aggregate root)
- **Review** (aggregate root) — owned by review-service; tenant-scoped course review with moderation lifecycle (pending/published/rejected); rating 1-5

### Assessment Domain
- **Assessment** (aggregate root)
- **Attempt** (aggregate root)
- **ExamSession** (aggregate root)

### Certification Domain
- **Certificate** ✅ (preserved aggregate root)
- **Badge** (aggregate root) — owned by badge-service; awarded on completion/achievement triggers

### Commerce Domain
**Country factory (Pakistan):** build_commerce_service_for_pakistan(default_provider="jazzcash") — only PK supported at domain layer currently. See ADR-001 Decision 8.

- **CheckoutSession** — CREATED → SUBMITTED (services/commerce/checkout.py)
- **Order** — CREATED → PENDING → PAID → FAILED → RECONCILED
- **Transaction** — PENDING → SUCCESS → FAILED → RETRYING → RECONCILED
- **Subscription** — TenantSubscription, CommerceSubscription
- **Invoice** (shared/models/invoice.py)

### Academy Ops Domain (Pakistan-specific)
Source: `services/academy-ops/service.py` domain_owner mapping

| Entity | Domain Owner |
|---|---|
| academy.branch | academy-ops |
| academy.batch | academy-ops |
| academy.timetable | academy-ops |
| academy.attendance | academy-ops |
| academy.teacher_assignment | academy-ops |
| academy.fee_tracking | academy-ops |
| student.profile | system-of-record |
| commerce.invoice | commerce-service |
| learning.* | learning-service |

---

## 6. Event Envelope (Canonical)

Source: `docs/anchors/event-envelope.md`

All events in the platform must use the 7-field canonical envelope:

```json
{
  "event_id": "string (UUID)",
  "event_type": "string (topic key from event_topics.json)",
  "timestamp": "ISO-8601 UTC",
  "tenant_id": "string (UUID)",
  "correlation_id": "string (UUID)",
  "payload": "object",
  "metadata": "object"
}
```

**Source of truth for topics:** `Repo/event_topics.json` — 39 topics; 0 phantom consumers (verified U7).

---

## 7. Known Domain Gaps

| Gap | Severity | Source |
|---|---|---|
| academy-ops has no HTTP API — programmatic access only | MEDIUM | U10 |
| system-of-record has no HTTP API — loaded by academy-ops only | MEDIUM | U10 |
| CheckoutService in-memory — no persistent Order/Transaction store | HIGH | U10 CF-007 |
| Commerce domain has no single HTTP entry point — split across 6 backend services | MEDIUM | U10 CF-001 |
| workflow-engine relationship to academy-ops event feeds undocumented | LOW | U10 |
