# FRONTEND PERMISSION MATRIX

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- USER_ROLES_AND_PERMISSIONS.md (permission model, authorize endpoint)
- API_CONTRACT.md (authorize request/response)
- FEATURE_SCOPE.md

---

## How Frontend Uses Permissions

Permissions are NOT hardcoded to roles. The frontend:

1. Calls `POST /api/v1/rbac/authorize` with `permission_key` + resource context
2. Evaluates `"decision": "allow"` or `"decision": "deny"`
3. Shows/hides UI elements based on the decision

This means any user can hold any permission (RBAC is policy-driven). The matrix below shows typical permission-to-role mappings as a guide only.

---

## Permission Key Convention

Format: `<resource_type>.<action>`

Examples: `course.publish`, `attendance.mark`, `audit.view_tenant`

---

## Permission Matrix

### Identity & Access Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `user.create` | "Invite user" button on /admin/users | Admin | low |
| `user.view` | User list, user profile read | Admin | low |
| `user.update` | Edit user profile form | Admin | low |
| `user.delete` | Deactivate user action | Admin | moderate |
| `user.manage_credentials` | Admin password reset button on /admin/users/:id | Admin | high |
| `session.view` | View session metadata (auth audit) | Admin | moderate |
| `session.revoke` | Revoke session button | Admin | high |

---

### RBAC Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `role.view` | Role list and role detail pages | Admin | low |
| `role.create` | "Create role" button on /admin/roles | Admin | moderate |
| `role.update` | Edit role form | Admin | moderate |
| `role.delete` | Soft-delete role button (system roles locked) | Admin | high |
| `permission.view` | Permissions catalog page | Admin | low |
| `permission.assign` | "Add permission" to role; "Assign role" to user | Admin | moderate |
| `role.manage_policy` | Policy rules management page | Admin | high |
| `audit.view_tenant` | Audit log page access | Admin | moderate |

---

### Tenancy Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `tenant.view` | Tenant detail page | Admin | low |
| `tenant.view_all` | Platform-wide tenant list (platform admin) | Platform Admin | high |
| `tenant.update` | Edit tenant configuration | Admin | moderate |
| `tenant.configure` | Tenant settings, feature flags | Admin | moderate |
| `tenant.manage_lifecycle` | Suspend/reactivate/archive buttons | Admin | critical |
| `org.view` | Organization hierarchy page | Admin | low |
| `org.manage` | Create/edit org units | Admin | moderate |

---

### Academy Operations Permissions (Pakistan)

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `branch.view` | Branch list, branch detail | Admin | low |
| `branch.create` | "Add branch" button | Admin | moderate |
| `branch.update` | Edit branch form | Admin | moderate |
| `batch.view` | Batch list, batch detail | Admin, Teacher (own) | low |
| `batch.create` | "Add batch" button | Admin | moderate |
| `batch.update` | Edit batch details | Admin | moderate |
| `timetable.view` | Timetable view tab | Admin, Teacher | low |
| `timetable.manage` | Add/remove timetable slots | Admin | moderate |
| `attendance.mark` | Attendance marking UI (date selector + roster) | Teacher | low |
| `attendance.view` | Attendance reports tab | Admin, Teacher | low |
| `fee.manage` | Fee structure configuration | Admin | moderate |

---

### Learning & Content Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `course.view` | Course list, course detail, learner catalog | All | low |
| `course.create` | "Create course" button | Admin | moderate |
| `course.update` | Course metadata edit form | Admin, Teacher (own) | moderate |
| `course.publish` | Publish/Unpublish button | Admin | moderate |
| `course.delete` | Delete course action | Admin | high |
| `lesson.view` | Lesson list, lesson player | Teacher, Learner | low |
| `lesson.create` | "Add lesson" button | Admin, Teacher | moderate |
| `lesson.update` | Lesson editor | Admin, Teacher | moderate |
| `content.view` | Content library access | All | low |
| `content.upload` | File upload button; media upload form | Admin, Teacher | moderate |
| `content.delete` | Delete content action | Admin | moderate |
| `program.view` | Program management | Admin | low |
| `program.manage` | Create/edit programs | Admin | moderate |
| `learning_path.view` | Learning path page | Admin, Learner | low |

---

### Enrollment & Progress Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `enrollment.view` | Enrollment list, student roster | Admin, Teacher (own batch) | low |
| `enrollment.create` | Admin-initiated enrollment; self-enroll button (learner) | Admin, Learner | low |
| `enrollment.update` | Enrollment status transitions | Admin | moderate |
| `progress.view` | Progress summary, progress bars | Admin (all), Teacher (class), Learner (own) | low |
| `progress.update` | Lesson complete action (learner-triggered) | Learner | low |

---

### Assessment & Certification Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `assessment.view` | Assessment list, assessment detail | Admin, Teacher | low |
| `assessment.create` | "Create assessment" button | Admin, Teacher | moderate |
| `assessment.update` | Edit assessment form | Admin, Teacher (own) | moderate |
| `assessment.grade` | Grade submission form; score entry | Admin, Teacher | moderate |
| `attempt.view` | Submission list; my attempt history (learner) | Admin, Teacher, Learner (own) | low |
| `attempt.create` | "Start assessment" button | Learner | low |
| `certificate.view` | Certificate list, certificate viewer | All | low |
| `certificate.issue` | Manual certificate issuance | Admin | moderate |
| `badge.view` | Badge list | All | low |
| `badge.issue` | Award badge action | Admin | moderate |

---

### Commerce & Billing Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `checkout.create` | Checkout flow (payment form) | Learner | low |
| `payment.view` | Payment history, order status | Admin (all), Learner (own) | low |
| `payment.initiate` | "Pay now" button; initiate-payment call | Learner | moderate |
| `billing.view` | Invoices list, billing overview | Admin | low |
| `billing.manage` | Create invoices | Admin | moderate |
| `subscription.view` | Subscription list | Admin | low |
| `subscription.manage` | Create/cancel subscriptions | Admin | moderate |
| `analytics.view_revenue` | Revenue dashboard, revenue summary widget | Admin | moderate |
| `reconciliation.view` | Reconciliation admin screen | Admin | moderate — FGAP-005 |

---

### Analytics & Reporting Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `analytics.view` | Analytics dashboard, all analytics widgets | Admin | low |
| `report.view` | Reports list, saved reports | Admin | low |
| `report.create` | Report builder | Admin | low |
| `skill_analytics.view` | Skill analytics page | Admin | low |

---

### AI Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `ai.use` | AI tutor chat panel; recommendations widget | Learner | low |
| `ai.configure` | AI settings configuration | Admin | moderate |
| `ai.generate_course` | AI course generation form | Admin | moderate |

---

### Notification Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `notification.view` | Notification inbox | All | low |
| `notification.manage` | Notification dispatch center; notification logs | Admin | moderate |
| `notification.send` | Manual notification trigger | Admin | moderate |

---

### Integration Permissions

| Permission Key | UI Element Gated | Typical Role | Risk Tier |
|---|---|---|---|
| `integration.manage` | Integration configuration page | Admin | high |
| `webhook.manage` | Webhook configuration | Admin | high |
| `feature_flag.manage` | Feature flag toggle | Admin | critical |
| `lti.configure` | LTI integration setup | Admin | high |
| `hris.sync` | HRIS sync trigger | Admin | moderate |

---

## Permission Check Implementation Rules

### Route Guard Pattern

```
// Before mounting any permission-gated route:
const decision = await fetch('/api/v1/rbac/authorize', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'X-Tenant-Id': tenantId },
  body: JSON.stringify({
    subject_type: 'user',
    subject_id: userId,
    permission_key: '<required_permission>',
    resource_type: '<resource>',
    resource_id: '<id or tenant_id>'
  })
});
if (decision.decision === 'deny') redirect('/403');
```

### Inline UI Guard Pattern

```
// Before rendering any gated button/section:
const decision = await batchAuthorize([
  { permission_key: 'course.publish', resource_type: 'course', resource_id: courseId },
  { permission_key: 'course.update', resource_type: 'course', resource_id: courseId }
]);
// Use POST /api/v1/rbac/authorize/batch for multiple checks per page
```

### Effective Permissions (Pre-fetch for Dashboard)

```
// At dashboard load:
GET /api/v1/rbac/subjects/user/{user_id}/effective-permissions?tenant_id={tenant_id}
→ Cache result; use to show/hide nav items without per-item round-trips
```

---

## Policy Rule UI Impact

Policy rules in rbac-service affect authorization decisions server-side. Frontend handles these outcomes:

| Rule Type | Frontend Handling |
|---|---|
| SOD_CONFLICT | 403 response → show "Action not permitted (conflict)" |
| EXPLICIT_DENY | 403 response → show "Access denied" |
| STEP_UP_REQUIRED | 403 with reason code → redirect to step-up auth (future MFA sprint) |
| TIME_WINDOW | 403 response outside window → show "Access not permitted at this time" |
| NETWORK_BOUNDARY | 403 response → show "Access denied from current network" |
