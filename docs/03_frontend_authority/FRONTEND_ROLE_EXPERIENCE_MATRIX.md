# FRONTEND ROLE EXPERIENCE MATRIX

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- USER_ROLES_AND_PERMISSIONS.md (scope types, role model)
- FEATURE_SCOPE.md
- FRONTEND_IMPACT_ANALYSIS.md (Phase 2.95 role experience table)
- POST_COLLAPSE_FRONTEND_READINESS.md

---

## Role Build Status

| Role | Build Status | RBAC Scope |
|---|---|---|
| Admin | ✅ Build now | `scope_type=TENANT` or `scope_type=ORG_UNIT` or `scope_type=BRANCH` |
| Teacher | ✅ Build now | `scope_type=BRANCH` or `scope_type=COHORT` or `scope_type=COURSE` |
| Learner | ✅ Build now | `scope_type=COURSE` or `scope_type=COHORT` |
| Parent/Guardian | ❌ FGAP-001 | TBD (parent sprint) |

---

## Matrix Legend

| Symbol | Meaning |
|---|---|
| ✅ Full | Full access to feature |
| 👁 View | Read-only access |
| ➕ Create | Create only |
| ✏️ Manage | Create + Edit + View |
| ❌ None | No access |
| 🔧 Configure | Admin-level configuration |
| GAP | FGAP — planned but requires sprint |

---

## Feature × Role Experience

| Feature Area | Admin | Teacher | Learner | Parent |
|---|---|---|---|---|
| **Authentication** | | | | |
| Login | ✅ Full | ✅ Full | ✅ Full | GAP (FGAP-001) |
| SSO login | ✅ Full | ✅ Full | ✅ Full | GAP |
| Password reset | ✅ Full | ✅ Full | ✅ Full | GAP |
| Admin password reset (other users) | ✅ Full | ❌ None | ❌ None | N/A |
| **Tenancy & Organization** | | | | |
| Tenant configuration | 🔧 Configure | ❌ None | ❌ None | N/A |
| Tenant lifecycle (suspend/archive) | 🔧 Configure | ❌ None | ❌ None | N/A |
| Organization hierarchy | ✏️ Manage | 👁 View | ❌ None | N/A |
| Department management | ✏️ Manage | ❌ None | ❌ None | N/A |
| Institution management | ✏️ Manage | ❌ None | ❌ None | N/A |
| **User Management** | | | | |
| View user list | ✅ Full | ❌ None | ❌ None | N/A |
| Create users | ➕ Create | ❌ None | ❌ None | N/A |
| Edit user profiles | ✏️ Manage | ❌ None | 👁 Own only | N/A |
| Manage role assignments | 🔧 Configure | ❌ None | ❌ None | N/A |
| Reset another user's password | ✅ Full | ❌ None | ❌ None | N/A |
| **RBAC & Access Control** | | | | |
| View roles | ✅ Full | ❌ None | ❌ None | N/A |
| Create / edit roles | 🔧 Configure | ❌ None | ❌ None | N/A |
| View permissions catalog | 👁 View | ❌ None | ❌ None | N/A |
| Manage policy rules | 🔧 Configure | ❌ None | ❌ None | N/A |
| View audit log | 👁 View (requires `audit.view_tenant`) | ❌ None | ❌ None | N/A |
| **Academy Operations (Pakistan)** | | | | |
| Manage branches | ✏️ Manage | ❌ None | ❌ None | N/A |
| Manage batches | ✏️ Manage | 👁 View own | ❌ None | N/A |
| Manage timetable | ✏️ Manage | 👁 View | ❌ None | GAP (child timetable) |
| Mark attendance | ❌ None | ✅ Full | ❌ None | GAP (child attendance) |
| View attendance | 👁 View | ✅ Full (own batch) | 👁 Own only | GAP |
| Manage fee structures | ✏️ Manage | ❌ None | ❌ None | N/A |
| **Courses & Content** | | | | |
| Browse course catalog | 👁 View | 👁 View | ✅ Full (browse + enroll) | GAP |
| Create course | ➕ Create | ❌ None | ❌ None | N/A |
| Edit course metadata | ✏️ Manage | ✏️ Own only | ❌ None | N/A |
| Publish / unpublish course | 🔧 Configure | ❌ None | ❌ None | N/A |
| Create lessons | ✅ Full | ✅ Own courses | ❌ None | N/A |
| Edit lessons | ✅ Full | ✅ Own courses | ❌ None | N/A |
| Upload content (video/docs/SCORM) | ✅ Full | ✅ Own courses | ❌ None | N/A |
| **Enrollment & Progress** | | | | |
| View all enrollments | ✅ Full | 👁 Own batch | ❌ None | GAP (child only) |
| Enroll learner (admin) | ➕ Create | ❌ None | ❌ None | N/A |
| Self-enroll (after payment if required) | ❌ None | ❌ None | ✅ Full | N/A |
| View progress | 👁 All | 👁 Own batch | 👁 Own only | GAP (child progress) |
| **Assessment & Certification** | | | | |
| Create assessments | ✅ Full | ✅ Full | ❌ None | N/A |
| Take assessments | ❌ None | ❌ None | ✅ Full | N/A |
| Grade submissions | ✅ Full | ✅ Full | ❌ None | N/A |
| View certificates | ✅ All | 👁 Own batch | 👁 Own only | GAP (child certs) |
| View badges | ✅ All | ❌ None | 👁 Own only | N/A |
| **AI Features** | | | | |
| AI tutor chat (lesson panel) | 🔧 Configure | ❌ None | ✅ Full | N/A |
| Course recommendations | 👁 View (reporting) | ❌ None | ✅ Full | N/A |
| AI course generation | ✅ Full | ❌ None | ❌ None | N/A |
| AI copilot overlay | N/A | N/A | GAP (FGAP-003) | N/A |
| **Commerce** | | | | |
| View invoices / billing | ✅ Full | ❌ None | 👁 Own payments | GAP (child fees) |
| Manage subscriptions | ✏️ Manage | ❌ None | ❌ None | N/A |
| Checkout (pay for course/batch) | ❌ None | ❌ None | ✅ Full | N/A |
| View order status | ✅ All | ❌ None | 👁 Own only | GAP |
| Revenue analytics | 👁 View | ❌ None | ❌ None | N/A |
| Reconciliation admin screen | GAP (FGAP-005) | ❌ None | ❌ None | N/A |
| **Analytics & Reporting** | | | | |
| Learning analytics dashboard | ✅ Full | 👁 Class-level | 👁 Own progress | GAP |
| Skill analytics | ✅ Full | 👁 Class-level | ❌ None | N/A |
| Report builder | ✅ Full | ❌ None | ❌ None | N/A |
| Risk insights | GAP (FGAP-004) | GAP (class-level) | ❌ None | N/A |
| **Notifications** | | | | |
| Receive notifications | ✅ Full | ✅ Full | ✅ Full | GAP |
| Manage notification settings | 🔧 Configure | ❌ None | 👁 Own prefs | N/A |
| Send notifications (dispatch) | 🔧 Configure | ❌ None | ❌ None | N/A |
| **Integrations** | | | | |
| LTI configuration | 🔧 Configure | ❌ None | ❌ None | N/A |
| HRIS sync configuration | 🔧 Configure | ❌ None | ❌ None | N/A |
| Webhook management | 🔧 Configure | ❌ None | ❌ None | N/A |
| **Platform Infrastructure** | | | | |
| Feature flag management | 🔧 Configure | ❌ None | ❌ None | N/A |
| Onboarding wizard | ✅ Full | ❌ None | ❌ None | N/A |
| System settings | 🔧 Configure | ❌ None | ❌ None | N/A |
| **Offline Mode** | | | | |
| Offline content access | N/A | N/A | GAP (FGAP-006) | N/A |

---

## Scope Disambiguation

RBAC scope types affect which data a user sees, even within the same role:

| Scope | Who | Effect |
|---|---|---|
| TENANT | Tenant admin | Sees all data across all branches, batches, users |
| ORG_UNIT | Org-level admin | Sees data within their org unit |
| BRANCH | Branch manager / HQ admin | Sees data for assigned branch_ids only |
| COHORT | Cohort-level teacher or tutor | Sees data for assigned cohort |
| COURSE | Course-specific teacher | Sees data for assigned course only |

Frontend must NOT hardcode scope-based filtering. All filtering is implicit via server-side RBAC enforcement on queries.

---

## First-Login Experience by Role

| Role | First Login Redirect | First Action |
|---|---|---|
| Admin (new tenant) | /admin/onboarding | Complete onboarding wizard |
| Admin (existing tenant) | /admin/dashboard | See tenant overview |
| Teacher | /teacher/dashboard | See my batches |
| Learner | /learner/dashboard | See enrolled courses (or course catalog if none) |
