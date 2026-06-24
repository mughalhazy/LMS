# FRONTEND WORKFLOW TO SCREEN MAP

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- PRODUCT_WORKFLOWS.md (WF-001 through WF-010)
- FULLSTACK_STITCHING_CONTRACT.md (FSC-001 through FSC-009)
- FRONTEND_SCREEN_CATALOG.md
- FRONTEND_ROUTE_CATALOG.md

---

## WF-001: Tenant Onboarding

**Trigger:** New education operator signs up

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Tenant registers | Signup form | `/signup` | `POST /api/v1/tenants` (+ Idempotency-Key) |
| 2. Auth user created | (automatic, backend) | — | — |
| 3. RBAC role assigned | (automatic, backend) | — | — |
| 4. Organization provisioned | (automatic, backend) | — | — |
| 5. Config resolved | (automatic, backend) | — | — |
| 6. Entitlement evaluated | (automatic, backend) | — | — |
| 7. Tenant ready → admin dashboard | Onboarding wizard | `/admin/onboarding` | onboarding-service (TBD) |

**Frontend role:** Signup form → collect `tenant_name`, `admin_email`, `admin_password`, `country_code` ("PK") → POST → receive session → redirect to onboarding wizard.

---

## WF-002: Academy Setup (Pakistan)

**Trigger:** Tenant admin sets up academy structure

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Create branch | Branch management | `/admin/branches/new` | academy-commerce-service POST (TBD) |
| 2. Create batch | Batch management | `/admin/batches/new` | academy-commerce-service POST (TBD) |
| 3. Assign teachers | Batch detail → Teachers tab | `/admin/batches/:id` | academy-commerce-service PATCH (TBD) |
| 4. Build timetable | Timetable screen | `/admin/batches/:id/timetable` | academy-commerce-service POST slot (TBD) |
| 5. Fee structure defined | Fee structure screen | `/admin/fee-structures` | academy-commerce-service POST (TBD) |

**Frontend role:** Admin builds the operational structure before students can enroll in academy batches.

---

## WF-003: Student Enrollment

**Trigger:** Student registers for a course or batch

### Path A — Course enrollment (Learning Runtime)

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Student authenticated | — | — | Session valid |
| 2. Entitlement checked | (background check) | — | entitlement-service (TBD) |
| 3. Course found | Course detail (learner) | `/learner/courses/:id` | course-service GET (TBD) |
| 4. Prerequisite check | (automatic, backend on enroll) | — | prerequisite-engine-service |
| 5. Enrollment created | Course detail — Enroll button | `/learner/courses/:id` | `POST /api/v1/enrollments` |
| 6. Progress initialized | (automatic, backend) | — | — |
| 7. Success → course player | Course player | `/learner/courses/:id/learn` | — |

### Path B — Academy batch enrollment (Pakistan academy)

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Student authenticated | — | — | — |
| 2. Batch selected | Batch catalog (TBD) | TBD | academy-commerce-service (TBD) |
| 3. Fee payment initiated | Checkout flow | `/learner/checkout` | `POST /api/v1/checkout/sessions` |
| 4. Payment confirmed | Order confirmation | `/learner/orders/:id` | `GET /api/v1/checkout/orders/:id` |
| 5. Enrollment granted | Success state → batch content | — | — |

---

## WF-004: Learning and Completion

**Trigger:** Enrolled student begins learning

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Launch content | Course player | `/learner/courses/:id/learn/:lid` | lesson-service GET, content-service GET |
| 2. Lesson progress recorded | Course player (automatic on progress) | — | `POST /api/v1/progress/lessons/:id/upsert` |
| 3. Lesson completed | Course player — Mark complete | — | `POST /api/v1/progress/lessons/:id/complete` |
| 4. Assessment triggered (if any) | Assessment player | `/learner/assessments/:id` | assessment-service GET (TBD) |
| 5. Attempt submitted | Assessment player — Submit | — | attempt-service POST (TBD) |
| 6. Score evaluated | Score result screen (post-submit) | (inline) | quiz-engine or exam-engine |
| 7. Certificate issued | Certificate screen | `/learner/certificates/:id` | certificate-service GET (TBD) |
| 8. Badge issued (optional) | Badge notification | Notification + `/learner/badges` | badge-service (TBD) |

**AI Tutor Panel** (on Step 1–3): embedded in course player; messages sent to ai-tutor-service; responses displayed inline.

---

## WF-005: Commerce Checkout (JazzCash/EasyPaisa)

**Trigger:** Student initiates payment for course or batch

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Create checkout session | Checkout — Step 1 | `/learner/checkout` | `POST /api/v1/checkout/sessions` |
| 2. Add product to session | Checkout — Step 2 | (same screen, step 2) | `POST /api/v1/checkout/sessions/:id/items` |
| 3. Submit session | Checkout — Submit | (same screen, step 3) | `POST /api/v1/checkout/sessions/:id/submit` |
| 4. Initiate payment | Payment screen | (same screen, step 4) | `POST /api/v1/checkout/orders/:id/initiate-payment` |
| 5. Poll for status | Payment pending screen | `/learner/orders/:id` | `GET /api/v1/checkout/orders/:id` (poll interval TBD) |
| 6a. PAID → success | Order success screen | `/learner/orders/:id` (PAID state) | — |
| 6b. FAILED → retry | Order failed screen with retry CTA | `/learner/orders/:id` (FAILED state) | Re-initiate payment |

**Idempotency:** Client generates `idempotency_key` (UUID v4) on session creation. Duplicate submits return existing Order.

---

## WF-006: Fee Tracking and Ledger

**Trigger:** Batch fee due or payment received

| Step | Screen | Route | API Call |
|---|---|---|---|
| Fee due | Admin billing view | `/admin/billing` | invoice-billing-service (TBD) |
| Invoice generated | Invoice detail | `/admin/billing/invoices/:id` | invoice-billing-service (TBD) |
| Payment received | (automatic via WF-005 or manual post) | — | financial-ledger-service (TBD) |
| Balance tracked | Revenue analytics | `/admin/revenue` | revenue-service (TBD) |

**Frontend role:** Admin views outstanding invoices and ledger. Learner pays via WF-005. System updates ledger automatically.

---

## WF-007: Notification Dispatch

**Trigger:** Domain event (backend-triggered)

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Event triggers notification | (backend) | — | — |
| 2. Notification dispatched | (backend) | — | — |
| 3. User views notification | Notification center | `/notifications` | notification-service GET (TBD) |
| 4. Admin views dispatch log | Admin notification center | `/admin/notifications` | notification-service GET (TBD) |

**Frontend role:** Notification center displays received notifications with channel indicators (WhatsApp, SMS, Email, Push). Frontend does NOT trigger notification dispatch directly — that is backend-driven by domain events.

---

## WF-008: Revenue Anomaly Detection

**Trigger:** Scheduled analytics run

| Step | Screen | Route | API Call |
|---|---|---|---|
| 1. Anomaly signals computed | (backend scheduled) | — | — |
| 2. Anomaly visible on dashboard | Admin dashboard → Revenue widget | `/admin/dashboard` | revenue-service (TBD) |
| 3. Admin drills into detail | Revenue analytics | `/admin/revenue` | revenue-service (TBD) |

**Signal types visible in UI:** unpaid installments, renewal-at-risk, revenue decline, churn signal.

---

## WF-009: Config and Entitlement Resolution

**Trigger:** Any service needs to determine if a capability is enabled for a tenant

This workflow is **backend-only** with one frontend manifestation:

| Step | Screen | Route | API Call |
|---|---|---|---|
| Entitlement gates feature | Any gated UI element | Various | `POST /api/v1/rbac/authorize` (RBAC); entitlement-service (capability gating) |
| Feature flag override | (backend resolution) | — | feature-flag-service (TBD) |
| Admin manages feature flags | Feature flags page | `/admin/feature-flags` | feature-flag-service (TBD) |
| Tenant config update | Settings page | `/admin/settings` | `PATCH /api/v1/tenants/:id/configuration` |

---

## WF-010: LTI Integration

**Trigger:** External LMS launches content via LTI 1.3

| Step | Screen | Route | API Call |
|---|---|---|---|
| LTI launch | LTI launch handler (special route) | `/lti/launch` (TBD) | lti-service (TBD) |
| Auth validated | (automatic) | — | — |
| Content launched | SCORM/content player | `/learner/courses/:id/learn/:lid` or SCORM iframe | scorm-service, content-service |
| Grade passback | (automatic on completion) | — | lti-service grade passback (TBD) |
| Admin configures LTI | Integration settings | `/admin/integrations` | lti-service config (TBD) |

---

## Critical User Journey to Screen Mapping

| CJ ID | Journey | Primary Screens | Routes |
|---|---|---|---|
| CJ-001 | Tenant signup → config → entitlement | Signup, Onboarding Wizard | /signup, /admin/onboarding |
| CJ-002 | Enroll → complete → certificate | Course detail, Course player, Certificate screen | /learner/courses/:id, /learner/courses/:id/learn/:lid, /learner/certificates/:id |
| CJ-003 | Course creation → catalog | Course management, Course detail (admin) | /admin/courses/new, /admin/courses/:id |
| CJ-004 | JazzCash checkout → enrollment | Checkout flow, Order status, Course player | /learner/checkout, /learner/orders/:id, /learner/courses/:id/learn |
| CJ-005 | LTI 1.3 launch → grade passback | LTI launch handler, Content player | /lti/launch, /learner/courses/:id/learn/:lid |
