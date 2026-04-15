# 0002 - User Service Projection Migration Notes

## Objective
Introduce a dedicated User Service projection store while keeping Rails `User` model as source identity entity.

## Plan
1. **Backfill projection rows** from Rails User read replicas into user-service datastore:
   - `tenant_id`, `user_id` (Rails PK), `email`, `username`
   - profile defaults and `status=provisioned`
2. **Enable dual-read verification**:
   - Compare projected identity attributes with Rails source on read paths.
3. **Cut over write paths**:
   - Route profile/status/linkage writes to user-service datastore only.
4. **Event subscribers**:
   - Subscribe downstream services to lifecycle events:
     - `lms.user.created`
     - `lms.user.profile.updated`
     - `lms.user.status.changed`
     - `lms.user.role.linked`
     - `lms.user.role.unlinked`
     - `lms.user.deleted`
5. **Deprecate legacy writes** after consistency SLOs are met.

## Guardrails
- No auth credential data stored.
- No RBAC policy engine data stored.
- No institution ownership records stored.
- No writes to shared Rails DB.
