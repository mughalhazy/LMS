# RBAC Authorization System Specification

## Roles, Permissions, and Scope

| role | permissions | scope |
|---|---|---|
| Platform Super Admin | `tenant.create`, `tenant.update`, `tenant.suspend`, `tenant.delete`, `tenant.view_all`, `platform.config.manage`, `audit.view_all`, `support.impersonate_readonly` | Global (all tenants, platform-level) |
| Tenant Admin | `tenant.settings.manage`, `org.user.invite`, `org.user.disable`, `org.role.assign`, `catalog.manage`, `program.manage`, `report.view_tenant`, `integration.manage_tenant` | Single tenant |
| Compliance Officer | `audit.view_tenant`, `audit.export`, `policy.view`, `policy.enforce.override_with_reason`, `report.compliance.view` | Single tenant (compliance domains) |
| Instructor | `course.create`, `course.update_owned`, `course.publish_owned`, `content.upload`, `assessment.create_owned`, `grade.manage_owned`, `learner.progress.view_assigned` | Assigned courses/programs within tenant |
| Teaching Assistant | `course.update_assigned`, `assessment.grade_assigned`, `learner.progress.view_assigned`, `discussion.moderate_assigned` | Assigned course sections within tenant |
| Learner | `course.view_enrolled`, `content.consume_enrolled`, `assessment.submit_enrolled`, `grade.view_self`, `certificate.view_self` | Self + enrolled courses within tenant |
| HR/People Manager | `learner.assign_training`, `learner.progress.view_team`, `report.team_completion.view`, `skill.gap.view_team` | Manager’s hierarchy/business unit within tenant |
| External Auditor (Read Only) | `audit.view_scoped`, `report.compliance.view_scoped`, `evidence.download_scoped` | Time-bound, policy-defined subset of tenant data |
| Service Account (Integration) | `api.client_credentials.use`, `user.provision`, `enrollment.sync`, `report.extract_scoped` | Tenant + API scopes explicitly granted to client |

## Role Assignments

1. **Subject types**: `user`, `group`, and `service_account` can receive role assignments.
2. **Assignment model**:
   - `direct`: role assigned directly to a subject.
   - `group-derived`: subject inherits role through identity-provider or LMS group membership.
   - `just-in-time`: temporary elevation with start/end time and approval record.
3. **Scope binding**:
   - Every assignment includes `scope_type` (`platform`, `tenant`, `org_unit`, `course`, `self`) and `scope_id`.
   - Effective access = role permissions constrained by assignment scope.
4. **Separation of duties**:
   - Conflicting role pairs (e.g., `Tenant Admin` + `External Auditor`) are blocked by policy.
5. **Lifecycle controls**:
   - Assignment creation/update/removal is audited.
   - Time-bound assignments auto-expire.
   - Disabled users lose all effective permissions immediately.

## Policy Enforcement

1. **Enforcement points**:
   - API Gateway performs token validation and coarse scope checks.
   - Service layer performs fine-grained authorization on every command/query.
   - Data layer enforces tenant/org-unit filters to prevent over-fetch.
2. **Decision flow**:
   - Authenticate principal.
   - Resolve all active role assignments.
   - Expand permissions from roles.
   - Apply deny rules, scope constraints, and contextual conditions.
   - Return `ALLOW` or `DENY` with reason code.
3. **Policy rules**:
   - Default deny.
   - Explicit deny overrides allow.
   - Least-privilege scopes are preferred (course/org-unit before tenant/global).
   - Sensitive actions (delete, publish, override) require step-up auth and justification.
4. **Context-aware checks**:
   - Tenant match required for all tenant resources.
   - Ownership/assignment checks for instructor/TA actions.
   - Relationship checks for manager access (team hierarchy).
   - Time/IP/device constraints for privileged roles when configured.
5. **Auditability**:
   - Every authorization decision logs principal, action, resource, scope, decision, policy ID, and correlation ID.
   - Denials are observable for alerting and compliance reviews.

## Minimal Authorization Data Model

- `roles(role_id, role_name, description)`
- `permissions(permission_id, action, resource_type)`
- `role_permissions(role_id, permission_id)`
- `assignments(assignment_id, subject_type, subject_id, role_id, scope_type, scope_id, starts_at, ends_at, assigned_by)`
- `policy_rules(policy_id, effect, condition_expr, priority)`
- `authz_audit_log(event_id, timestamp, principal, action, resource, scope, decision, reason)`
