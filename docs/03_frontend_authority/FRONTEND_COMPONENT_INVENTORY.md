# FRONTEND COMPONENT INVENTORY

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Purpose

Documents the common reusable UI components needed across screens. This is a logical inventory — not a design spec. No React/Flutter code. Derived from the patterns common across FRONTEND_SCREEN_CATALOG.md, FRONTEND_PERMISSION_MATRIX.md, and FRONTEND_WORKFLOW_TO_SCREEN_MAP.md.

---

## Component Categories

1. Authentication components
2. Navigation components
3. Layout components
4. Data display components
5. Form components
6. Permission guard components
7. State placeholder components
8. Commerce components
9. Learning runtime components
10. AI components

---

## 1. Authentication Components

### AuthGuard

- Purpose: Wraps every authenticated route. Checks for valid access token. Redirects to /login on expiry.
- Inputs: child route component
- Behavior: read access_token from store; if expired → attempt refresh via POST /api/v2/sessions/refresh; if refresh fails → redirect /login
- Used by: ALL non-public routes

### TenantGuard

- Purpose: Validates X-Tenant-Id is present on all API calls.
- Inputs: tenant_id from session store
- Behavior: inject X-Tenant-Id header into all outgoing requests; block requests if tenant_id not set

### PermissionGuard

- Purpose: Gate component rendering on a permission check result.
- Inputs: permission_key, resource_type, resource_id, fallback (optional)
- Behavior: call POST /api/v1/rbac/authorize; render children if "allow"; render fallback or null if "deny"
- Used by: buttons, tabs, sections, nav items

### TokenRefreshBanner

- Purpose: Alert when session is approaching expiry (last 5 minutes).
- Inputs: token_expires_at
- Behavior: countdown display; "Stay logged in" CTA triggers refresh

---

## 2. Navigation Components

### SidebarNav

- Purpose: Role-aware vertical navigation.
- Inputs: user role, effective permissions list
- Behavior: render navigation tree filtered to items user has permission to see. Uses effective-permissions cache from dashboard load. Does NOT make per-item authorize calls.
- Variants: AdminSidebar, TeacherSidebar, LearnerSidebar

### TopBar

- Purpose: Global top navigation bar.
- Contains: tenant logo, notification bell (unread count), user avatar + dropdown (profile, logout), search (TBD scope)
- Used by: all authenticated layouts

### BreadcrumbTrail

- Purpose: Show current navigation path.
- Inputs: route segments
- Used by: all admin screens; course player

### NotificationBell

- Purpose: Show unread notification count badge; open notification drawer.
- Inputs: unread_count from notification-service
- Behavior: poll or websocket-subscribe to notification updates (polling interval TBD)

---

## 3. Layout Components

### AdminLayout

- Purpose: Shell for all admin pages. Left sidebar + top bar + content area.
- Contains: SidebarNav (AdminSidebar), TopBar, main content slot

### TeacherLayout

- Purpose: Shell for all teacher pages.
- Contains: SidebarNav (TeacherSidebar), TopBar, main content slot

### LearnerLayout

- Purpose: Shell for all learner pages.
- Contains: SidebarNav (LearnerSidebar), TopBar, main content slot

### PublicLayout

- Purpose: Shell for unauthenticated pages (login, forgot-password).
- Contains: brand area, centered card

### TwoColumnLayout

- Purpose: Split layout for detail pages (list + detail, player + sidebar).
- Used by: Course player, audit log, grading screen

---

## 4. Data Display Components

### DataTable

- Purpose: Paginated list view with sort, filter, search.
- Inputs: columns, rows, total, page, page_size, onPageChange, onSort
- Behavior: handle pagination shape `{ items, page, page_size, total }`. Render rows when items.length > 0 even if total = 0 (stub workaround).
- Used by: User list, course list, enrollment list, audit log, role list, invoice list

### StatCard

- Purpose: Single KPI display (number + label + trend arrow).
- Inputs: label, value, unit (PKR or %), trend (up/down/flat)
- Used by: All dashboards

### WidgetContainer

- Purpose: Dashboard widget wrapper. Handles its own loading/error state independently.
- Inputs: title, loading, error, children
- Behavior: show skeleton on loading; show widget error (not page error) on API failure

### StatusBadge

- Purpose: Colored status pill.
- Variants: active/inactive/pending/paid/failed/revoked (each has a distinct color)
- Used by: user status, enrollment status, order status, session status

### ProgressBar

- Purpose: Linear completion percentage bar.
- Inputs: value (0–100), label
- Used by: Learner dashboard, course player

### EmptyState

- Purpose: Illustration + message when list/view has no data.
- Inputs: title, description, optional CTA button
- Used by: all list screens

---

## 5. Form Components

### ControlledInput

- Purpose: Text/email/password input with validation error display.
- Inputs: name, label, type, rules, error
- Used by: Login form, user forms, assessment forms

### FileUpload

- Purpose: Drag-drop file upload with progress indicator.
- Inputs: accept (MIME types), maxSize, onUpload
- Behavior: POST to media-service (binary); then POST metadata to content-service
- Used by: Content upload screen

### RoleAssignmentForm

- Purpose: Select role + scope type + resource IDs for a user assignment.
- Inputs: userId, available roles, scope types
- API: POST /api/v1/rbac/assignments
- Used by: User detail screen

### TimetableSlotForm

- Purpose: Add a timetable slot: day of week, start_time, end_time, subject.
- Inputs: batch_id, teacher_ids
- API: academy-commerce-service POST slot (TBD)
- Used by: Timetable screen

### CheckoutForm

- Purpose: Multi-step payment form (cart → submit → pay).
- Contains: CartSummary, PaymentMethodSelector (JazzCash/EasyPaisa), IdempotencyKeyGenerator
- API: checkout-service (WF-005 flow)
- Used by: Checkout screen

---

## 6. Permission Guard Components

### ShowIfAllowed

- Purpose: Inline component that renders children only when permission check returns "allow".
- Inputs: permission_key, resource_type, resource_id, fallback
- Behavior: calls POST /api/v1/rbac/authorize; shows children or fallback
- Used by: all action buttons, tabs requiring elevated access

### HideIfDenied

- Purpose: Render null if permission denied. No fallback.
- Inputs: permission_key, resource_type, resource_id
- Used by: Nav items, action buttons that should simply not appear (not disabled)

### DisableIfDenied

- Purpose: Render children disabled (greyed) if permission denied.
- Inputs: permission_key, resource_type, resource_id
- Used by: Publish button, Delete button (show as disabled, not hidden, for discoverability)

---

## 7. State Placeholder Components

### LoadingSkeleton

- Purpose: Content-shaped placeholder during data fetch.
- Variants: TableSkeleton, CardSkeleton, TextSkeleton, WidgetSkeleton

### ErrorBanner

- Purpose: Inline error display for API failures.
- Inputs: message, retry (optional callback)
- Used by: All data-fetching screens

### ForbiddenScreen (403)

- Purpose: Full-page access denied.
- Behavior: shows reason if policy rule provides reason code; navigate-back CTA

### NotFoundScreen (404)

- Purpose: Full-page not found.

---

## 8. Commerce Components

### PaymentMethodSelector

- Purpose: Select JazzCash or EasyPaisa; collect payment details.
- Context: Pakistan-only. No cards.
- Used by: Checkout screen

### OrderStatusPoller

- Purpose: Poll GET /api/v1/checkout/orders/:id at interval; render PENDING/PAID/FAILED states.
- Inputs: order_id, polling_interval_ms
- Behavior: stop polling when terminal state reached (PAID or FAILED)
- Used by: Order status screen

### CartSummary

- Purpose: Display line items + total (PKR).
- Used by: Checkout screen

### InvoiceRow

- Purpose: Single invoice line item in billing list.
- Inputs: invoice_id, amount (PKR), status, due_date
- Used by: Admin billing screen, learner payment history

---

## 9. Learning Runtime Components

### LessonNavigator

- Purpose: Sidebar showing lesson list with completion status for current course.
- Inputs: course_id, lessons[], current_lesson_id
- Behavior: highlight current; show check if `progress.status = "completed"`
- Used by: Course player

### VideoPlayer

- Purpose: Video player for lesson content.
- Inputs: content_url, onProgress(pct), onComplete
- Behavior: call POST /api/v1/progress/lessons/:id/upsert at regular intervals; call /complete on end

### ScormPlayer

- Purpose: SCORM 2004 iframe player via scorm-service.
- Inputs: scorm_package_url, lesson_id
- Behavior: communicate with scorm-service API for completion signal

### AssessmentRenderer

- Purpose: Render quiz or exam questions.
- Inputs: assessment_type (quiz/exam), questions[], time_limit
- Used by: Assessment player

### CertificateViewer

- Purpose: Render certificate with learner name, course, date, and download PDF.
- Inputs: certificate_id, learner_name, course_name, issue_date
- Used by: Certificate screen

---

## 10. AI Components

### AiTutorPanel

- Purpose: Side panel on course player for per-lesson text chat with ai-tutor-service.
- Inputs: lesson_id, user_id, tenant_id
- Behavior: send message to ai-tutor-service; display response; maintain message history
- Permission gate: `ai.use`
- FGAP boundary: Tutor chat only (not full copilot). FGAP-003 is the copilot overlay — additive.
- Used by: Course player (SCR-018)

### RecommendationCard

- Purpose: Display a recommended course with rationale.
- Inputs: course_id, course_title, reason
- Used by: Learner dashboard

---

## Component Architecture Constraints

1. No component may contain hardcoded role_key strings. Use PermissionGuard with permission_key only.
2. No component may hardcode tenant_id. Inject from session store.
3. All API calls must include Authorization + X-Tenant-Id headers from global API client.
4. AuthGuard wraps the entire router — individual components do not handle token expiry.
5. DataTable must handle `total = 0` gracefully (stub — see API_CONTRACT.md pagination note).
6. AI components are optional slots — screens must render without them if ai-tutor-service is unavailable.
