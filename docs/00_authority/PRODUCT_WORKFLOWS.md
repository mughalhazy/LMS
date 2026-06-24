# PRODUCT_WORKFLOWS

Status: Active
Authority Level: High
Last Reviewed: 2026-06-21
Owner: Shared

---

## Source Authority

Extracted from: docs/architecture/, services/academy-ops/service.py (U10), services/commerce/service.py (U10), services/commerce/checkout.py (U10), docs/anchors/, U9 critical user journeys

---

## Overview

This document captures the primary product workflows as verified from repository evidence. Unverified steps are marked TBD – REQUIRES VERIFICATION.

---

## WF-001: Tenant Onboarding

**Trigger:** New education operator signs up

```
1. Tenant registers → tenant-service creates tenant record
   - Fields: tenant_id (UUID), name, country_code (PK), segment_type, plan_type, addon_flags
2. Auth user created → auth-service provisions admin user
3. RBAC role assigned → rbac-service assigns ADMIN role to founding user
4. Organization provisioned → org-service creates root org node
5. Config resolved → config-service resolves effective config for PK/segment/plan
6. Entitlement evaluated → entitlement-service determines which capabilities are enabled
7. Tenant ready → academy-ops or backend commerce can begin
```

**Events emitted:** CONFIRMED NONE via Kafka event bus. infrastructure/event-bus/event_topics.json (39 topics) contains no tenant.created or onboarding events. WF-001 is a synchronous service chain only (tenant-service → auth-service → rbac-service → org-service → config-service → entitlement-service). No domain event emission on tenant onboarding.
**Pakistan-specific:** country_code="PK" triggers PK config layer resolution
**Services involved:** tenant-service, auth-service, rbac-service, org-service, config-service, entitlement-service, onboarding-service

---

## WF-002: Academy Setup (Pakistan Academy Ops)

**Trigger:** Tenant admin sets up their academy structure

```
1. Create branch → AcademyOpsService.create_branch(tenant_id, branch_data)
2. Create batch → AcademyOpsService.create_batch(branch_id, batch_data)
3. Assign teachers → AcademyOpsService.assign_teacher_to_batch(...)
4. Build timetable → AcademyOpsService.create_timetable_slot(...)
   - Conflict detection runs automatically
5. Fee structure defined → AcademyOpsService.set_fee_structure(...)
```

**Evidence source:** services/academy-ops/service.py (1357 lines; domain_owner mapping)
**Note:** academy-ops has no HTTP API — academy-commerce-service is the HTTP entry point that wraps AcademyOpsService calls. Direct programmatic access is only via backend wrappers.
**Events emitted:** feeds to ("system-of-record", "workflows", "operations-os")

---

## WF-003: Student Enrollment

**Trigger:** Student registers for a course or batch

**Path A — Course enrollment (Learning Runtime):**
```
1. Student authenticated (auth-service, JWT RS256)
2. Entitlement checked → entitlement-service.is_enabled(tenant_id, capability)
3. Course found → course-service
4. Prerequisite check → prerequisite-engine-service
5. Enrollment created → enrollment-service (API: POST /api/v2/enrollments)
6. Progress record initialized → progress-service
7. Event: lms.enrollment.created → analytics, certificate-service listeners
```

**Path B — Academy batch enrollment (Pakistan academy):**
```
1. Student authenticated
2. AcademyOpsService called (via academy-commerce-service)
3. Fee payment initiated → WF-005 (JazzCash checkout)
4. Payment confirmed → AcademyOpsService.record_student_enrollment(...)
5. SOR updated → SystemOfRecord.record_enrollment(...)
6. Timetable access granted
```

**Services involved:** auth-service, entitlement-service, course-service, prerequisite-engine-service, enrollment-service, progress-service, academy-ops (for academy path)

---

## WF-004: Learning and Completion

**Trigger:** Enrolled student begins learning

```
1. Student launches content → content-service or scorm-service
2. Lesson progress recorded → progress-service
   - Each lesson completion emits: lms.lesson.completed.v1 or lms.progress.lesson_completed.v1
   [NOTE: Duplicate topic — OI-001 from U7, unresolved]
3. Assessment triggered (optional) → assessment-service
4. Attempt submitted → attempt-service
5. Score evaluated → exam-engine or quiz-engine
6. Course completion detected → progress-service (emits `lms.progress.course_completed.v1`)
7. Certificate issued → certificate-service
   - Event: lms.certificate.issued
8. Badge issued (optional) → badge-service
```

**Events involved:** lms.lesson.completed.v1 (lesson-service), lms.progress.lesson_completed.v1 (progress-service), lms.progress.course_completed.v1 (progress-service), lms.enrollment.enrollment_status_updated.v1 (enrollment-service), lms.certificate.issued
**Evidence:** docs/anchors/event-envelope.md, event_topics.json (39 topics, 0 phantom consumers — U7)

---

## WF-005: Commerce Checkout (Pakistan — JazzCash/EasyPaisa)

**Trigger:** Student or admin initiates payment for course/batch enrollment

**Domain layer (services/commerce/):**
```
1. build_commerce_service_for_pakistan(default_provider="jazzcash") called
2. CheckoutService.start_session(session_id, tenant_id, learner_id, product_id, idempotency_key)
3. CatalogService.resolve_sellable_product(tenant_id, product_id)
4. CheckoutService.calculate_total(products)
5. CheckoutService.submit_session(session_id, max_retries=2)
   - Payment executed via integrations/payments/orchestration.py
   - Retry with exponential backoff (on retryable failures)
   - Idempotency: (tenant_id, idempotency_key) → return existing Order if duplicate
6. Order status: CREATED → PAID (or FAILED)
7. If PAID: enrollment granted; event emitted
8. ReconcileOrder when payment webhook confirms → Order: PAID → RECONCILED
```

**NOTE:** CheckoutService persistence: SAFE-DEFAULT (Phase 3.25). SQLite persistence sprint will add SQLiteCheckoutStore using BaseRepository pattern (same as 16 wired services). No owner decision required. In-memory is acceptable for development phase.

**JazzCash webhook flow:** CONFIRMED via code inspection. PaymentReconciliationEngine in integrations/payments/reconciliation.py receives payment events. run_reconciliation_pass() updates Order status to RECONCILED after PAID confirmation. Test: integrations/payments/test_reconciliation.py (confirmed active). Domain layer: services/commerce/apply_reconciliation() applies reconciliation to commerce store.

**Services involved:** checkout-service, payment-service, academy-commerce-service (HTTP layer); services/commerce/ (domain layer); integrations/payments/ (JazzCash/EasyPaisa adapters)

---

## WF-006: Fee Tracking and Ledger

**Trigger:** Batch fee due or payment received

```
1. Fee structure defined in academy-ops
2. Fee due event → AcademyOpsService generates invoice
3. Invoice posted → SystemOfRecord.post_invoice_to_ledger(...)
4. Payment received → SystemOfRecord.post_payment_to_ledger(...)
5. Outstanding balance tracked in system-of-record ledger
6. Financial ledger updated → financial-ledger-service (HTTP layer)
```

**Evidence:** services/academy-ops/service.py (fee_tracking domain), services/system-of-record/service.py (post_invoice_to_ledger, post_payment_to_ledger methods)

---

## WF-007: Notification Dispatch

**Trigger:** Domain event (attendance, payment due, course completion, etc.)

```
1. Domain event received → notification-service
2. Workflow determined → NotificationOrchestrator (services/notification-service/orchestration.py)
   - persona-based command shortcuts (routes by learner/parent/teacher persona)
3. Channel selected → ChannelActionRouter
   - Fallback order: WhatsApp → SMS → Email
4. Adapter invoked → integrations/communication/
   - WhatsAppAdapter, SMSAdapter, EmailAdapter
5. Delivery attempt logged
```

**Warning:** notification-service uses HS256 JWT (platform debt — R-012)

---

## WF-008: Revenue Anomaly Detection

**Trigger:** Scheduled analytics run or on-demand call

```
1. CommerceService.detect_revenue_anomalies(tenant_id, window_days=30)
2. Four signal categories evaluated:
   - unpaid_installment: installment plans with overdue payments
   - renewal_at_risk: subscriptions approaching expiry without renewal
   - revenue_decline: revenue dropped >20% vs prior period
   - churn_signal: user activity drop correlated with subscription end
3. Anomaly events emitted via publish_event (best-effort — silently fails if backend/shared absent)
```

**Evidence:** services/commerce/service.py (443 lines)

---

## WF-009: Config and Entitlement Resolution

**Trigger:** Any service needs to determine if a capability is enabled for a tenant

```
1. Normalize context: {tenant_id, country_code, segment_type, plan_type, addon_flags}
2. Read capability definition → CapabilityRegistryService.get_capability(capability_key)
3. Resolve effective config → ConfigService.resolve(ConfigResolutionContext)
   - Layers: global → country → segment → tenant (deep-merge, 4 levels)
4. Evaluate entitlement → EntitlementService.is_enabled(tenant_id, capability_key)
5. Assemble final_state → ENABLED only if all three checks pass
```

**Evidence:** docs/anchors/capability-resolution.md; services/config-service/service.py; services/entitlement-service/service.py

---

## WF-010: LTI Integration

**Trigger:** External LMS launches content via LTI

```
1. LTI launch request received → lti-service
2. Auth validated (LTI-specific nonce, LTI nonce stored in Redis TTL=600s per U9 H-010)
3. Context mapped to tenant
4. Content launched → content-service or scorm-service
5. Grade passback → lti-service (on completion)
```

**Evidence:** docs/integrations/lti-consumer-spec.md, docs/integrations/lti-provider-spec.md

---

## Critical User Journeys (from U9 Test Suite Plan)

| ID | Journey | Services |
|---|---|---|
| CJ-001 | Tenant signup → config → entitlement | tenant, auth, config, entitlement |
| CJ-002 | Enroll → complete → certificate | enrollment, progress, certificate |
| CJ-003 | Course creation → catalog | course, content, catalog |
| CJ-004 | JazzCash checkout → enrollment | checkout, payment, enrollment (via commerce) |
| CJ-005 | LTI 1.3 launch → grade passback | lti-service |
