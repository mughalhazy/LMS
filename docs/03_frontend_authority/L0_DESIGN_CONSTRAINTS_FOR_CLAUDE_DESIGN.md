# L0 DESIGN CONSTRAINTS FOR CLAUDE DESIGN

Status: FROZEN
Date: 2026-06-24
Phase: Phase 3.5 — L0 Frontend Authority Input Freeze
Audience: Claude Design Agent
Authority: L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md

---

## Purpose

This document is the prescriptive constraint set for the Claude Design agent. It defines what MUST be true in every design output, what MUST NOT appear, and the rules that govern all design decisions for Meridian LMS Sprint 1.

Claude Design MUST NOT invent anything not listed in this document or in the L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md source. Every screen, route, workflow, role, permission, and API in the design output must trace to a named source in the L0 freeze.

---

## Section 1: Non-Negotiable Architecture Constraints

These constraints are architectural facts. They are not design preferences. Every design output must be consistent with all 5.

### C-001: JWT Identity Model

- `access_token.sub` = `session_id` (NOT user_id)
- `user_id` is available only in the login API response at `response.user.user_id`
- `tenant_id` is available only in the login API response at `response.user.tenant_id`
- User roles are NOT in the login response — they must be fetched via `GET /api/v1/rbac/assignments?subject_id=&tenant_id=`
- **Design implication:** Post-login, the app must make an RBAC assignments call before rendering role-specific navigation. Show a loading state while roles are being resolved.

### C-002: Required Headers on Every Authenticated Request

Every API call except the exempt paths below must include:

```
Authorization: Bearer <access_token>
X-Tenant-Id: <tenant_id>
Content-Type: application/json
```

**Exempt paths (no auth headers required):**
- `POST /api/v2/auth/sessions/login`
- `POST /api/v2/auth/tokens/refresh`
- All `/public/*` routes

**Design implication:** Session expiry (401 response) must display a non-disruptive refresh attempt first, then redirect to login only if refresh fails. Never redirect to login on the first 401.

### C-003: Permission-Based Navigation

- All route guards and UI element visibility are driven by `POST /api/v1/rbac/authorize`
- NO hardcoded role_key strings anywhere in the frontend
- Each navigation item and each gated action requires an authorize call
- Batch authorize: multiple permission keys can be checked in one call for dashboard prefetch

**Design implication:** Navigation menus are dynamic. They render based on what the authorize endpoint permits. Do not design static nav menus with role_key conditionals. Design a single nav structure that the permission system populates.

**Authorization check pattern:**
```
POST /api/v1/rbac/authorize
{
  "subject_id": "<user_id>",
  "tenant_id": "<tenant_id>",
  "resource_type": "<resource_type>",
  "action": "<action>",
  "resource_id": "<optional>"
}
Response: { "allowed": true/false }
```

### C-004: API Version Exceptions

- Auth service: `/api/v2/auth/` (NOT /api/v1/)
- Session service: `/api/v2/sessions/` (NOT /api/v1/)
- All other services: `/api/v1/`

**Design implication:** Error handling must know which base path to use per service. Token refresh is a v2 call.

### C-005: Pagination — `total` Is Always 0

All list endpoints return:
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

The `total` field always returns 0. It is a known backend limitation.

**Design implication:**
- NEVER render "0 results" or "No items found" when `items` is non-empty
- Pagination must be derived from whether `items.length < page_size` (no next page) rather than from `total`
- Do not display "Page 1 of X" total page count — it will always show 0

---

## Section 2: What Claude Design MUST NOT Invent

Claude Design operates exclusively within the L0 freeze. Violations invalidate the design output.

### 2.1 Routes

- Do not invent new routes
- All routes are defined in L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md
- Any route not in the matrix does not exist for Sprint 1

### 2.2 Screens

- Do not invent new screens
- All 27 screens are defined in FRONTEND_SCREEN_CATALOG.md (SCR-001 through SCR-027)
- Do not combine screens that are defined as separate
- Do not split screens that are defined as single

### 2.3 Workflows

- Do not invent new workflows
- All 10 workflows are defined in FRONTEND_WORKFLOW_TO_SCREEN_MAP.md (WF-001 through WF-010)
- Do not add steps to existing workflows

### 2.4 Roles

- Sprint 1 roles are exactly: Admin, Teacher, Learner
- Do not design for Parent/Guardian — FGAP-001 (deferred)
- Do not design for Super Admin as a separate role — it is an admin with TENANT scope
- Do not invent any other role

### 2.5 Permissions

- All permission keys are defined in FRONTEND_PERMISSION_MATRIX.md
- Format: `<resource_type>.<action>`
- Do not invent new permission keys
- Do not use role_key as a permission mechanism

### 2.6 APIs

- All confirmed API endpoints are in L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md Section 13
- 19 BACKEND-TBD services have screens but no confirmed endpoints — stub these
- Do not invent endpoint paths
- Do not assume REST conventions for TBD services

---

## Section 3: Required State Requirements Per Screen Type

Every screen design must account for all applicable states. Missing a state is a design gap.

### 3.1 States Required on All Authenticated Screens

| State | When | Display |
|---|---|---|
| Loading | API call in flight | Skeleton loader or spinner — never blank |
| Empty | API returns `items: []` | Empty state illustration + CTA (not "0 results") |
| Error | API returns 4xx/5xx (non-auth) | Error message + retry button |
| Unauthorized | authorize endpoint returns `allowed: false` | Access denied message + back navigation |
| Success | Data loaded | Populated content |

### 3.2 Additional States for Specific Screen Types

**List screens (user list, course list, enrollment list, etc.):**
- Pagination controls when `items.length === page_size` (may be more)
- Search/filter empty state: "No results for [query]" with clear filter option
- Loading per page (not just first load)

**Form screens (create/edit screens):**
- Validation error state (inline, per field)
- Submission loading state (button disabled + spinner)
- Submission success state (confirmation + redirect or message)
- Submission failure state (server error message, form remains populated)

**Dashboard screens (DASH-001 through DASH-004):**
- Per-widget loading state (widgets load independently)
- Per-widget error state (widget shows error inline, does not crash page)
- Empty dashboard state (first-time admin/teacher before data exists)

**Payment screens (WF-005 checkout flow):**
- PENDING: Payment processing spinner, auto-poll message ("Verifying payment...")
- PAID: Success confirmation with order summary
- FAILED: Failure message with retry option and support contact

**Course player / lesson screen (SCR-020):**
- Loading lesson content state
- Content render error state
- Progress save confirmation (toast or indicator)
- Completion celebration state (on lesson complete)

### 3.3 Token Refresh State

When a 401 is received on any authenticated call:
1. Attempt token refresh silently (no UI change)
2. Retry the original request
3. If refresh fails: redirect to login with session-expired message
4. Never show raw 401 error to the user

---

## Section 4: FGAP-Excluded Elements

These elements MUST NOT appear in Sprint 1 designs. They are formally deferred.

### FGAP-001: Parent/Guardian Portal

- NO `/parent/*` routes in navigation
- NO parent login screen
- NO parent dashboard
- NO "view as parent" option
- NO child progress view from parent perspective
- Workaround: `/parent/*` routes return 404

### FGAP-002: Adaptive Learning Path

- NO adaptive learning path widget on learner dashboard
- NO "recommended next" path UI
- NO dynamic lesson sequencing indicator
- Workaround: Show static lesson order in course structure. No adaptive path indicator.

### FGAP-003: AI Copilot Overlay

- NO global floating AI copilot icon
- NO "Ask AI" button accessible from all screens
- NO multi-context AI overlay component
- IN SCOPE: `AiTutorPanel` within the lesson/course player screen ONLY
- Workaround: AiTutorPanel in course player is the complete AI feature for Sprint 1.

### FGAP-004: Risk Insights Dashboard

- NO "at-risk learner" widget on admin dashboard
- NO "at-risk learner" widget on teacher dashboard
- NO risk score display on any screen
- NO learner risk analytics view
- Workaround: Dashboards render without risk widget. No placeholder shown.

### FGAP-005: Reconciliation Admin Screen

- NO `/admin/reconciliation` nav item in sidebar
- NO reconciliation audit screen in admin navigation
- STUB: Route `/admin/reconciliation` exists but returns 503 with "Coming soon" message
- Workaround: No nav item. Route is a backend stub.

### FGAP-006: PWA Offline Mode

- NO "Download for offline" button
- NO offline availability indicator
- NO offline mode toggle
- NO service worker cache UI
- NO sync status indicator
- Workaround: App is online-only. Standard browser behavior for offline state.

---

## Section 5: Payment Flow Constraints

WF-005 (Checkout and Payment) is a confirmed workflow with exact state machine.

### 5.1 Checkout Flow Sequence (MUST follow exactly)

```
1. POST /api/v1/checkout/sessions          → create session
2. POST /api/v1/checkout/sessions/{id}/items → add items
3. POST /api/v1/checkout/sessions/{id}/submit → lock session
4. POST /api/v1/checkout/sessions/{id}/initiate-payment → initiate payment (JazzCash/EasyPaisa)
5. GET  /api/v1/checkout/orders/{order_id}  → poll for status
```

### 5.2 Payment Methods — Pakistan Only

- JazzCash: Primary payment method — ALWAYS shown first
- EasyPaisa: Secondary payment method — ALWAYS shown second
- Currency: PKR only — no USD, no EUR, no other currency
- NO international payment methods (no Stripe, no PayPal, no credit card international)
- NO cryptocurrency
- Amount display: Format as `PKR X,XXX` (not $, not ₹)

### 5.3 Payment Status States

| State | API value | UI |
|---|---|---|
| Processing | `PENDING` | Spinner + "Verifying payment with [JazzCash/EasyPaisa]..." |
| Success | `PAID` | Success screen with order summary, enrollment confirmation |
| Failure | `FAILED` | Error screen with reason (if available), retry button, support link |

### 5.4 Poll Behavior

- Poll `GET /api/v1/checkout/orders/{order_id}` every 3 seconds maximum
- Maximum 20 polls (60 seconds) before showing timeout message
- Timeout message: "Payment verification is taking longer than expected. Please check your JazzCash/EasyPaisa app or contact support."
- Do not block UI during polling — show inline spinner

---

## Section 6: AI Feature Scope Constraints

### 6.1 In Scope for Sprint 1

- `AiTutorPanel`: Text chat interface within the lesson/course player screen (SCR-020)
  - Attached to lesson player — not a global overlay
  - One conversation thread per lesson session
  - Text-only input and response

### 6.2 Out of Scope (FGAP-003)

- Global AI copilot overlay accessible from any screen
- AI chat accessible outside the lesson player
- Voice or image AI interaction
- AI course recommendations widget (recommendation-service API is BACKEND-TBD)
- AI-generated course builder UI (course-generation-service API is BACKEND-TBD)

### 6.3 BACKEND-TBD AI Services

These AI features have screens and intent but confirmed API endpoints are not yet available:
- AI tutor chat: `POST /ai-tutor` — endpoint path TBD
- Recommendations: `GET /recommendations` — endpoint path TBD

Design for these screens with stub API placeholders. Show a loading/unavailable state if the API is not responding.

---

## Section 7: API Stub Handling Rules for BACKEND-TBD Services

19 services have confirmed screens but unconfirmed API endpoints. These rules govern how to design for them.

### 7.1 Stub Design Rule

For any screen backed by a BACKEND-TBD service:
- Design the screen layout completely (it is in scope)
- Stub API calls with a loading state that shows "Loading..." or skeleton
- If API call fails (404/503), show: "This feature is being connected. Check back soon." — NOT a generic error
- Do not remove the screen from navigation
- Do not hide the screen

### 7.2 BACKEND-TBD Service List

| Screen | Service |
|---|---|
| User management | user-service |
| Course management | course-service |
| Lesson management | lesson-service |
| Content upload | content-service + media-service |
| Assessment management | assessment-service |
| Assessment grading | attempt-service |
| Certificate view | certificate-service |
| Notifications | notification-service |
| AI tutor chat | ai-tutor-service |
| Recommendations | recommendation-service |
| Academy operations | academy-commerce-service |
| Revenue analytics | revenue-service |
| Billing/invoices | invoice-billing-service |
| Feature flags | feature-flag-service |
| Learning analytics | learning-analytics-service |
| Skill analytics | skill-analytics-service |
| LTI config | lti-service |

---

## Section 8: Pakistan Commerce Context Constraints

### 8.1 Currency

- PKR (Pakistani Rupee) only
- All prices formatted as: `PKR X,XXX` or `Rs. X,XXX`
- No decimal places for PKR amounts under PKR 1,000 unless required
- No foreign currency display or conversion

### 8.2 Payment Methods

- JazzCash first (most common in Pakistan)
- EasyPaisa second
- No other payment methods — not Stripe, not international cards, not bank transfer UI

### 8.3 Phone Numbers

- Pakistani phone number format: `+92 3XX-XXXXXXX`
- Validation: 11 digits starting with 03 (or +92 3)
- JazzCash and EasyPaisa require phone numbers in this format

### 8.4 Locale

- Primary language: English (Urdu i18n is MO-041, formally deferred)
- Date format: DD/MM/YYYY (Pakistan convention)
- Time format: 12-hour with AM/PM or 24-hour — consistent within the app
- No RTL layout required for Sprint 1 (Urdu RTL is deferred with MO-041)

### 8.5 Academic Calendar

- Pakistani academic year: April–March (or institution-specific)
- Term labels: Term 1, Term 2, Term 3 (or custom per institution)
- No US/EU academic calendar assumptions

---

## Section 9: Technical Design Context

These are the frontend framework constraints the design output must be compatible with.

| Factor | Value |
|---|---|
| Framework | Next.js 16 (App Router) |
| UI library | React 19 |
| Styling | Tailwind CSS v4 |
| Rendering | SSR for public pages; CSR for authenticated dashboard |
| Auth pattern | JWT in httpOnly cookie or memory (not localStorage) |
| State management | React Context + server components where applicable |
| Component model | Atomic design (atoms → molecules → organisms → pages) |

### 9.1 Design Implication: Next.js App Router

- Each route segment maps to a `page.tsx`
- Nested layouts (`layout.tsx`) handle persistent UI (nav, sidebar)
- Dynamic routes use `[param]` segments
- Loading UI uses `loading.tsx` at each segment — design must account for segment-level loading

### 9.2 Design Implication: Server vs. Client Components

- Public marketing pages: server components (no interactivity)
- Authenticated dashboard pages: client components (dynamic permission checks, real-time updates)
- Navigation guard: client component (needs access to token)

---

## Section 10: Scope Boundaries — What This Sprint Covers

### In Scope

- Admin role: Full coverage — all admin screens, all admin dashboards, all admin workflows
- Teacher role: Full coverage — all teacher screens, teacher dashboard, all teacher workflows
- Learner role: Full coverage — all learner screens, learner dashboard, all learner workflows
- All 10 workflows (WF-001 through WF-010)
- All 27 screens (SCR-001 through SCR-027)
- All 4 dashboards (DASH-001 through DASH-004)
- All ~95 routes

### Out of Scope for Sprint 1 (HARD BOUNDARY)

- Parent portal (FGAP-001)
- Adaptive learning path UI (FGAP-002)
- AI copilot overlay (FGAP-003)
- Risk insights widgets (FGAP-004)
- Reconciliation admin screen (FGAP-005)
- PWA offline mode (FGAP-006)
- Urdu i18n / RTL layout (MO-041 — formally deferred)
- Vocational certification templates (MO-042 — formally deferred)
- Marketplace/third-party courses (MO-043 — formally deferred)
- Offline box hardware integration (MO-044 — formally deferred)

---

## Constraint Checklist for Design Review

Before submitting any design output, verify:

- [ ] Every screen traces to SCR-001 through SCR-027
- [ ] Every route traces to FRONTEND_ROUTE_CATALOG.md
- [ ] No parent portal elements present
- [ ] No global AI copilot overlay present
- [ ] No risk insights widgets on dashboards
- [ ] No reconciliation nav item present
- [ ] No PWA/offline UI elements present
- [ ] Loading state defined for every screen
- [ ] Empty state defined for every list screen
- [ ] Error state defined for every screen
- [ ] Unauthorized state defined for every gated screen
- [ ] Payment flow uses exactly: JazzCash first, EasyPaisa second, PKR only
- [ ] Payment states: PENDING, PAID, FAILED all designed
- [ ] `total: 0` pagination handled — no "0 results" when items non-empty
- [ ] Token refresh flow shown (silent retry before login redirect)
- [ ] RBAC authorize call shown in auth flow before nav renders
- [ ] No hardcoded role_key strings in any nav design

---

## Document Authority

This document freezes all design constraints as of 2026-06-24. No design output may introduce constraints, exceptions, or allowances not listed here. Any perceived gap in this document must be escalated before design output is produced — not resolved by the design agent independently.
