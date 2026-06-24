# FRONTEND DASHBOARD CATALOG

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- FEATURE_SCOPE.md §1.9 (analytics)
- PRODUCT_WORKFLOWS.md (WF-008 revenue anomaly)
- FRONTEND_IMPACT_ANALYSIS.md (Phase 2.95 dashboard composition)
- SERVICE_CATALOG.md (analytics/reporting services)
- FRONTEND_SCREEN_CATALOG.md

---

## DASH-001: Admin Dashboard

| Field | Value |
|---|---|
| **ID** | DASH-001 |
| **Route** | `/admin/dashboard` |
| **Target role** | Admin |
| **Purpose** | Tenant-wide operational overview |

### Widgets

| Widget | Description | Data Source | Permission |
|---|---|---|---|
| Tenant Overview | Active users, tenant plan, status | tenant-service GET /api/v1/tenants/:id/lifecycle | `analytics.view` |
| Enrollment Stats | Total enrollments, active enrollments, completions | enrollment-service GET /api/v1/enrollments (agg) | `analytics.view` |
| Revenue Summary | Total revenue (PKR), last 30 days, trend | revenue-service (TBD) | `analytics.view_revenue` |
| Branch Summary | Active branches count, top branch enrollment | academy-commerce-service (TBD) | `branch.view` |
| Notification Status | Recent dispatch count, failed deliveries | notification-service (TBD) | `notification.manage` |
| Active Users (7-day) | Count of users active in last 7 days | learning-analytics-service (TBD) | `analytics.view` |
| Recent Assessments | Latest assessment submissions | assessment-service (TBD) | `assessment.view` |
| AI Recommendations Alert | If recommendation-service reports low engagement | recommendation-service (TBD) | `analytics.view` |

### KPIs

| KPI | Target | Source |
|---|---|---|
| Monthly Active Learners | Trend up | learning-analytics-service |
| Course Completion Rate | % enrolled who completed | progress-service + enrollment-service |
| Revenue This Month | PKR total | revenue-service |
| Outstanding Fees | Overdue invoices count | invoice-billing-service |

### Actions

| Action | Route |
|---|---|
| Manage users | /admin/users |
| View all branches | /admin/branches |
| View revenue detail | /admin/revenue |
| View analytics | /admin/analytics |

### Navigation Paths

- Top nav → Admin Dashboard
- Login success redirect (admin role)

### Gap Widgets (FGAP — not in initial build)

| Widget | Gap |
|---|---|
| Learner risk insights | FGAP-004 |
| Reconciliation status | FGAP-005 |

---

## DASH-002: Teacher Dashboard

| Field | Value |
|---|---|
| **ID** | DASH-002 |
| **Route** | `/teacher/dashboard` |
| **Target role** | Teacher |
| **Purpose** | Class management overview |

### Widgets

| Widget | Description | Data Source | Permission |
|---|---|---|---|
| My Batches | List of batches assigned to me | academy-commerce-service (TBD) | `batch.view` |
| Today's Classes | Timetable slots for today | academy-commerce-service (TBD) | `timetable.view` |
| Upcoming Assessments | Assessments due in next 7 days | assessment-service GET (TBD) | `assessment.view` |
| Recent Submissions | Latest student submissions to grade | attempt-service GET (TBD) | `assessment.grade` |
| Attendance Summary | Attendance % last 30 days | academy-commerce-service (TBD) | `attendance.view` |
| Content Upload Status | Recently uploaded content | content-service (TBD) | `content.view` |

### KPIs

| KPI | Source |
|---|---|
| Batches assigned | academy-commerce-service |
| Ungraded submissions | attempt-service |
| Average attendance % | academy-commerce-service |

### Actions

| Action | Route |
|---|---|
| Mark today's attendance | /teacher/batches/:id/attendance |
| Grade submissions | /teacher/assessments/:id/grade |
| Add lesson | /teacher/courses/:id/lessons/new |

### Gap Widgets (FGAP — not in initial build)

| Widget | Gap |
|---|---|
| At-risk learner list (class-level) | FGAP-004 |

---

## DASH-003: Learner Dashboard

| Field | Value |
|---|---|
| **ID** | DASH-003 |
| **Route** | `/learner/dashboard` |
| **Target role** | Learner |
| **Purpose** | Personalized learning home page |

### Widgets

| Widget | Description | Data Source | Permission |
|---|---|---|---|
| Enrolled Courses | My active courses with progress bars | `GET /api/v1/enrollments?learner_id=`, `GET /api/v1/progress/learners/:id` | `course.view`, `progress.view` |
| Progress Summary | Overall completion %, in-progress, completed | `GET /api/v1/progress/learners/:id` | `progress.view` |
| AI Recommendations | Recommended next courses/content | recommendation-service (TBD) | `course.view` |
| AI Tutor Access | Quick-link to last active lesson tutor session | ai-tutor-service (TBD) | `ai.use` |
| Upcoming Assessments | Assessments due in next 7 days | assessment-service (TBD) | `attempt.view` |
| Certificates | Recently earned certificates | certificate-service (TBD) | `certificate.view` |
| Payment History | Recent payments and outstanding fees | `GET /api/v1/checkout/orders/:id` | `payment.view` |
| Notifications | Unread notification count | notification-service (TBD) | `notification.view` |

### KPIs

| KPI | Source |
|---|---|
| Courses in progress | enrollment-service |
| Overall completion % | progress-service |
| Certificates earned | certificate-service |

### Actions

| Action | Route |
|---|---|
| Continue learning | /learner/courses/:id/learn/:lesson_id |
| Enroll in new course | /learner/courses |
| View certificate | /learner/certificates/:id |
| Pay outstanding fee | /learner/checkout |

### Gap Widgets (FGAP — not in initial build)

| Widget | Gap |
|---|---|
| Offline content library | FGAP-006 |
| Adaptive learning path | FGAP-002 |

---

## DASH-004: Analytics Dashboard (Admin)

| Field | Value |
|---|---|
| **ID** | DASH-004 |
| **Route** | `/admin/analytics` |
| **Target role** | Admin |
| **Purpose** | Deep learning analytics and reporting |

### Widgets

| Widget | Description | Data Source | Permission |
|---|---|---|---|
| Enrollment Trends | Enrollments over time (weekly/monthly) | learning-analytics-service (TBD) | `analytics.view` |
| Course Completion Rate | By course, by cohort | learning-analytics-service (TBD) | `analytics.view` |
| Assessment Scores | Score distribution | assessment-service (TBD) | `analytics.view` |
| Skill Analytics | Skill coverage across learners | skill-analytics-service (TBD) | `analytics.view` |
| Revenue Trend | Revenue over time, by product | revenue-service (TBD) | `analytics.view_revenue` |
| Active Users | DAU / WAU / MAU | learning-analytics-service (TBD) | `analytics.view` |

### Actions

| Action | Route |
|---|---|
| Build report | /admin/analytics/reports |
| Export data | report download (TBD) |
| View skill analytics | /admin/analytics/skills |

---

## Dashboard Gap Summary

| Gap | Dashboard Impact |
|---|---|
| FGAP-001 | No parent dashboard |
| FGAP-002 | No adaptive learning widget on learner dashboard |
| FGAP-003 | No copilot access point (additive to learner dashboard — won't affect existing widgets) |
| FGAP-004 | No risk widget on admin/teacher dashboards |
| FGAP-005 | No reconciliation widget on admin dashboard |
| FGAP-006 | No offline mode indicator |
