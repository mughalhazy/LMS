# L0 CLAUDE DESIGN BRIEF

Status: FROZEN
Date: 2026-06-24
Phase: Phase 3.5 — L0 Frontend Authority Input Freeze
Audience: Claude Design Agent (primary), Claude Code Agent (secondary)
Authority: L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md

---

## Mission

Design the Sprint 1 frontend of **Meridian LMS** — a Pakistan-first, multi-tenant SaaS Learning Management System.

The design must be production-ready, permission-driven, and mobile-responsive. It covers three user roles: Admin, Teacher, and Learner. Every screen, route, workflow, and permission in this brief is already defined. Your mission is to design them faithfully — not to discover, invent, or extend scope.

---

## Section 1: Product Context

### What Meridian LMS Is

Meridian LMS is a multi-tenant SaaS platform for educational institutions in Pakistan — academies, coaching centers, schools. Each tenant (institution) gets an isolated workspace with its own admin, teachers, and learners.

**Pakistan-first means:**
- JazzCash and EasyPaisa are the only payment methods
- Currency is PKR only
- Phone numbers are Pakistani format (+92)
- No international payment methods, no foreign currencies
- Designed for Pakistani internet speeds and device distribution

**Multi-tenant means:**
- Every API call carries `X-Tenant-Id` header
- Tenant scope is enforced server-side — no cross-tenant data is ever visible
- Admin scope varies: TENANT (all branches) / ORG_UNIT (a division) / BRANCH (single branch)

### What It Is Not

- Not a MOOC platform (not public course marketplace)
- Not a university portal (no academic records, no transcripts)
- Not a video conferencing tool
- Not a real-time collaboration tool
- Not internationalized for markets outside Pakistan in Sprint 1

---

## Section 2: Sprint 1 Scope

### Roles in Sprint 1

| Role | Scope | Primary Responsibility |
|---|---|---|
| Admin | TENANT / ORG_UNIT / BRANCH | Institution management: staff, branches, courses, commerce, analytics |
| Teacher | BRANCH / COHORT / COURSE | Teaching: courses, lessons, assessments, learner progress |
| Learner | COURSE / COHORT | Learning: enrollments, course player, assessments, certificates |

**Not in Sprint 1:** Parent/Guardian portal (FGAP-001 — separate sprint)

### Screen Count

- **27 screens total** (SCR-001 through SCR-027)
- **4 dashboards** (DASH-001 through DASH-004)
- **~95 routes**
- **10 workflows** (WF-001 through WF-010)

---

## Section 3: User Roles and Primary Journeys

### Admin

**First login experience:** Role selection → organization setup wizard → branch creation → invite teachers

**Primary journeys (design these first):**

**CJ-001: Admin Onboarding**
- Login → Role-based redirect → Admin Dashboard
- Dashboard shows: branch count, learner count, revenue summary, recent enrollments
- First-run: Setup wizard prompts to create first branch and invite first teacher

**CJ-002: Course Enrollment** (via Admin)
- Enrollment management screen → select learner → select course → confirm enrollment
- Admin can enroll on behalf of learners
- Route: `/admin/enrollments`

**Admin nav items (confirmed):**
- Dashboard
- Users (Admins, Teachers, Learners sub-items)
- Branches
- Courses
- Cohorts
- Enrollments
- Assessments
- Analytics
- Commerce (Checkout, Orders, Fees)
- Settings (Roles, Permissions, Feature Flags, LTI)

---

### Teacher

**First login experience:** Role resolution → Teacher Dashboard → View assigned courses

**Primary journeys:**

**CJ-003: Lesson Delivery**
- Teacher Dashboard → My Courses → Select Course → Lesson Management → Create/Edit Lesson → Publish
- Route: `/teacher/courses/{id}/lessons`

**Teacher nav items (confirmed):**
- Dashboard
- My Courses
- Lesson Management
- Assessments
- Learner Progress
- Attendance
- Timetable
- Notifications

---

### Learner

**First login experience:** Role resolution → Learner Dashboard → View enrolled courses

**Primary journeys:**

**CJ-004: Course Consumption**
- Learner Dashboard → My Courses → Select Course → Course Player → Lesson → Progress saved → Completion

**CJ-005: Self-Enrollment**
- Course Catalog → Browse → Select Course → Checkout → Payment (JazzCash/EasyPaisa) → Enrollment Confirmation → Start Course

**Learner nav items (confirmed):**
- Dashboard
- My Courses
- Course Catalog
- Assessments
- Certificates
- Notifications

---

## Section 4: Design Priorities

Design in this order. Priority 1 must be design-complete before Priority 3 begins.

### Priority 1: Auth and Navigation Foundation

These are structural — everything depends on them.

1. Login screen (SCR-001): `POST /api/v2/auth/sessions/login`
2. Post-login redirect: RBAC assignments call → role detection → dashboard redirect
3. Role-based navigation shell (sidebar + top nav) for Admin, Teacher, Learner
4. Token refresh silent behavior on 401
5. Unauthorized state (when `authorize` returns `allowed: false`)

### Priority 2: Core Dashboards

All 4 dashboards must be designed before individual screens.

1. DASH-001: Admin Dashboard — branch metrics, revenue summary, enrollment summary, active learner count
2. DASH-002: Teacher Dashboard — assigned courses, learner progress summary, upcoming timetable
3. DASH-003: Learner Dashboard — enrolled courses, progress bars, upcoming assessments, certificate count
4. DASH-004: Analytics Dashboard — revenue trends, enrollment trends, completion rates, assessment performance

Note: Exclude FGAP widgets. See L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md Section 4 for excluded elements.

### Priority 3: Key User Journeys

Design the end-to-end journeys listed in Section 3 (CJ-001 through CJ-005) as connected screen flows, not isolated screens.

### Priority 4: Remaining Screens

Complete all 27 screens. Use the L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md as the master reference for which screens exist.

### Priority 5: BACKEND-TBD Screens

Design the screens backed by BACKEND-TBD services (see L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md Section 7). Show full layout with stub loading/unavailable states for API content.

---

## Section 5: Key Technical Design Context

| Factor | Value | Design Impact |
|---|---|---|
| Framework | Next.js 16 (App Router) | Route segments map to `page.tsx`. Layouts persist across segments. |
| UI | React 19 + Tailwind CSS v4 | Utility-first. No UI framework lock-in. |
| Rendering | SSR (public) + CSR (auth) | Design auth pages as client-rendered — they need token access. |
| Auth | JWT in memory or httpOnly cookie | No localStorage. Session info only accessible after login response. |
| Permissions | `POST /api/v1/rbac/authorize` | Nav items render dynamically based on permission responses. |
| Mobile | Responsive — mobile-first | Pakistan device distribution skews mobile. Design mobile-first. |
| Pagination | `total` always 0 | Use `items.length < page_size` as "no more pages" indicator. |

---

## Section 6: The 10 Workflows — Design Reference

Every workflow below maps to screens in the design. Each must be traceable end-to-end.

| ID | Name | Entry Screen | Key Steps |
|---|---|---|---|
| WF-001 | Tenant Onboarding | Login | Login → Role redirect → Setup wizard → Org structure |
| WF-002 | Course Creation | Teacher Dashboard | Create course → Add modules → Add lessons → Publish |
| WF-003 | Learner Enrollment | Enrollment screen | Select learner → Select course → Confirm → Enrolled |
| WF-004 | Lesson Delivery | Lesson management | Open course → Create lesson → Add content → Publish |
| WF-005 | Checkout and Payment | Course catalog | Select course → Checkout → JazzCash/EasyPaisa → Poll → Result |
| WF-006 | Assessment Lifecycle | Assessment screen | Create assessment → Publish → Learner attempts → Grade → Result |
| WF-007 | Certificate Issuance | Progress view | Complete course → Trigger certificate → View/Download cert |
| WF-008 | RBAC Role Assignment | Settings → Roles | Select user → Assign role → Set scope → Confirm |
| WF-009 | Analytics Review | Analytics dashboard | Open analytics → Filter by date/branch/course → View charts |
| WF-010 | Attendance Management | Teacher timetable | Open session → Mark attendance → Save → View summary |

---

## Section 7: Deferred Features — Do Not Design

The following features are formally deferred (FGAPs). They must not appear in Sprint 1 design output.

| FGAP | Feature | What is Missing | Workaround in Sprint 1 |
|---|---|---|---|
| FGAP-001 | Parent Portal | No backend, no routes, no screens | `/parent/*` returns 404. No nav item. |
| FGAP-002 | Adaptive Learning Path | No adaptive-learning-service | Static lesson order. No adaptive indicator. |
| FGAP-003 | AI Copilot Overlay | No ai-copilot-service | AiTutorPanel in lesson player only. No global overlay. |
| FGAP-004 | Risk Insights Dashboard | No risk-scoring-service | Dashboards render without risk widget. |
| FGAP-005 | Reconciliation Screen | No HTTP endpoint | Route returns 503. No nav item. |
| FGAP-006 | PWA Offline Mode | No service worker | Online only. No offline UI. |

---

## Section 8: The 27 Screens — Summary Reference

Full screen specifications are in FRONTEND_SCREEN_CATALOG.md. The table below is the design brief summary.

| ID | Screen Name | Role | Route |
|---|---|---|---|
| SCR-001 | Login | Public | `/login` |
| SCR-002 | Admin Dashboard | Admin | `/admin/dashboard` |
| SCR-003 | User Management | Admin | `/admin/users` |
| SCR-004 | Role & Permission Management | Admin | `/admin/settings/roles` |
| SCR-005 | Branch Management | Admin | `/admin/branches` |
| SCR-006 | Cohort Management | Admin | `/admin/cohorts` |
| SCR-007 | Course Management (Admin) | Admin | `/admin/courses` |
| SCR-008 | Enrollment Management | Admin | `/admin/enrollments` |
| SCR-009 | Analytics Dashboard | Admin | `/admin/analytics` |
| SCR-010 | Commerce / Orders | Admin | `/admin/commerce/orders` |
| SCR-011 | Fees Management | Admin | `/admin/fees` |
| SCR-012 | Feature Flag Settings | Admin | `/admin/settings/feature-flags` |
| SCR-013 | LTI Configuration | Admin | `/admin/settings/lti` |
| SCR-014 | Teacher Dashboard | Teacher | `/teacher/dashboard` |
| SCR-015 | My Courses (Teacher) | Teacher | `/teacher/courses` |
| SCR-016 | Lesson Management | Teacher | `/teacher/courses/{id}/lessons` |
| SCR-017 | Assessment Management | Teacher | `/teacher/assessments` |
| SCR-018 | Learner Progress (Teacher view) | Teacher | `/teacher/progress` |
| SCR-019 | Learner Dashboard | Learner | `/learner/dashboard` |
| SCR-020 | Course Player / Lesson View | Learner | `/learner/courses/{id}/lessons/{lid}` |
| SCR-021 | Course Catalog | Learner | `/learner/catalog` |
| SCR-022 | My Enrollments | Learner | `/learner/enrollments` |
| SCR-023 | Assessment Attempt | Learner | `/learner/assessments/{id}/attempt` |
| SCR-024 | Certificate View | Learner | `/learner/certificates/{id}` |
| SCR-025 | Checkout Flow | Shared | `/checkout` |
| SCR-026 | Timetable / Schedule | Shared | `/timetable` |
| SCR-027 | Attendance View | Shared | `/attendance` |

---

## Section 9: Handoff from L0 to Design Sprint

### What L0 Has Established (Frozen)

- All routes (~95) with permission keys, primary APIs, role hints
- All screens (27) with states, actions, error conditions
- All workflows (10) with step-by-step screen and API mapping
- All permissions (12 categories, all keys in `<resource_type>.<action>` format)
- All confirmed API endpoints (auth, rbac, enrollment, progress, checkout)
- All FGAP deferred items with workarounds
- All architecture constraints (JWT, headers, pagination, v2 exceptions)
- Pakistan commerce context (JazzCash/EasyPaisa/PKR)

### What Claude Design Produces

Using L0 as the only source of truth:

1. **Wireframes** for all 27 screens — all states (loading, empty, error, unauthorized, success)
2. **Navigation flows** — role-based nav menus (Admin, Teacher, Learner)
3. **Workflow diagrams** — screen-to-screen flows for WF-001 through WF-010
4. **Component inventory** — named reusable components per screen
5. **Responsive layouts** — mobile-first, then desktop
6. **Interaction states** — form validation, submission, payment polling, token refresh

### What Claude Design Does NOT Produce

- Application code (that is Claude Code's phase)
- New product requirements
- New API endpoints
- New screens or routes beyond the 27/95 frozen
- Design for deferred features (FGAPs)

### What Claude Code Receives from Design

- Screen-by-screen component breakdown
- Interaction state designs (loading, error, empty, success)
- Navigation structure and guard logic flow
- Payment flow visual state machine
- RBAC authorize integration points per screen

---

## Section 10: L0 Frozen Declaration

This brief represents the complete, frozen frontend input for Sprint 1 of Meridian LMS as of 2026-06-24.

All inputs have been derived from 13 authority source documents:

1. FRONTEND_AUTHORITY_MASTER.md
2. FRONTEND_ROUTE_CATALOG.md
3. FRONTEND_SCREEN_CATALOG.md
4. FRONTEND_DASHBOARD_CATALOG.md
5. FRONTEND_NAVIGATION_MODEL.md
6. FRONTEND_ROLE_EXPERIENCE_MATRIX.md
7. FRONTEND_PERMISSION_MATRIX.md
8. FRONTEND_WORKFLOW_TO_SCREEN_MAP.md
9. FRONTEND_API_DEPENDENCY_MAP.md
10. FRONTEND_GAP_REGISTER.md
11. POST_COLLAPSE_FRONTEND_READINESS.md
12. PRODUCT_DECISION_REGISTER.md
13. DETERMINISM_CERTIFICATION_REPORT.md

No frontend-impacting gaps remain unclassified. All 6 FGAPs are non-blocking with documented workarounds. All 19 BACKEND-TBD services have defined screens and stub handling rules. All 8 determinism domains are certified DETERMINED.

```
L0 FROZEN
Date: 2026-06-24
Phase: Phase 3.5 — L0 Frontend Authority Input Freeze
Verdict: L0 FROZEN — All 4 output documents complete
```

Claude Design is cleared to begin Sprint 1 wireframing using this brief and L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md as the binding constraints.
