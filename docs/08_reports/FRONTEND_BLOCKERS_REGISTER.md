# FRONTEND BLOCKERS REGISTER

Status: Complete
Date: 2026-06-23
Phase: Phase 2.9 — Pre-Frontend Gate
Owner: AI

---

## Purpose

This register catalogs every item that blocks frontend development from beginning. An item is a frontend blocker only if:
- A frontend developer cannot proceed without the item being resolved, OR
- Starting frontend with the item unresolved would cause work that must be immediately thrown away

Items that are "nice to have" or "best practice" but do not stop frontend work are NOT blockers.

---

## Hard Blockers

Items that MUST be resolved before any frontend contract can be coded.

### BLOCK-001 (APPLIED IN PFDA): Login Response Shape Corrected

| Field | Value |
|---|---|
| **ID** | BLOCK-001 |
| **Issue** | Auth contract documented incorrect login response shape: `roles[]` at root level, missing `user` sub-object, missing `refresh_expires_in`. |
| **Evidence** | `auth-service/app/main.py` `/api/v1/auth/login` return shape: `{"session_id", "access_token", "refresh_token", "expires_in", "refresh_expires_in", "token_type", "user": {"user_id", "tenant_id", "email"}}`. Roles absent from login response — separate endpoint. |
| **Resolution** | APPLIED in PFDA: AUTH_AND_TENANCY_CONTRACT.md and DATA_SHAPE_REGISTRY.md updated. Frontend must implement `response.user.user_id` not `response.user_id`. |
| **Status** | RESOLVED |

---

### BLOCK-002 (APPLIED IN PFDA): JWT `sub` Claim Corrected

| Field | Value |
|---|---|
| **ID** | BLOCK-002 |
| **Issue** | Auth contract documented `sub` claim as UUID or opaque token. Code shows `sub = session_id` (not user_id). |
| **Evidence** | `auth-service/app/main.py` JWT building: `"sub": session.session_id`. |
| **Resolution** | APPLIED in PFDA: AUTH_AND_TENANCY_CONTRACT.md updated: sub = session_id. Any frontend code parsing `sub` for user identity must use `user_id` from the user sub-object of login response instead. |
| **Status** | RESOLVED |

---

### BLOCK-003 (OA-001): notification-service ASGI Shim

| Field | Value |
|---|---|
| **ID** | BLOCK-003 |
| **Issue** | notification-service could not start under uvicorn. Any frontend feature requiring in-app notifications would call a non-functional service. |
| **Resolution** | FIXED in Phase 2.9: FastAPI ASGI shim added to notification-service/app/main.py. Service is now uvicorn-deployable. |
| **Status** | RESOLVED |

---

### BLOCK-004 (OA-004): 3 Services Undeployable (service:ClassName)

| Field | Value |
|---|---|
| **ID** | BLOCK-004 |
| **Issue** | capability-registry, config-service, and entitlement-service had invalid manifest entries (`service:ClassName` format) with no runtime loader. Any frontend feature depending on capability gating or config resolution would fail silently. |
| **Resolution** | FIXED in Phase 2.9: ASGI shims added to all 3 services; service-manifest.json updated to `backend/services/<name>` paths with `app.main:app` modules. |
| **Status** | RESOLVED |

---

### BLOCK-005 (OA-009): session-service v2 URL — Contract Gap

| Field | Value |
|---|---|
| **ID** | BLOCK-005 |
| **Issue** | session-service uses `/api/v2/sessions`. Frontend built with `/api/v1/sessions` would 404 on all session calls. |
| **Resolution** | DOCUMENTED in Phase 2.9: api-versioning-strategy.md §5 now explicitly states the v2 exception. Frontend must use `/api/v2/sessions/`. |
| **Status** | RESOLVED |

---

## Soft Blockers (Documented — Not Hard Blockers)

Items that can be worked around during initial frontend development but must be resolved before production.

| ID | Item | Workaround |
|---|---|---|
| SB-001 | branch_ids missing from RBAC create API | Branch-scoped role assignment UI can be deferred; FIXED in Phase 2.9 anyway |
| SB-002 | 53 services with in-memory stores | Data lost on restart; acceptable in development but not production |
| SB-003 | Event delivery cross-service broken | In-process bus only; notification of cross-service events (e.g., enrollment → cert) will not fire in dev |
| SB-004 | session-service v2 / all others v1 | Now documented; frontend must handle this split deliberately |

---

## Previously Reported Blockers — Status

| Old Ref | Was a Blocker | Status |
|---|---|---|
| PFDA BLOCK-001 | Login response shape | RESOLVED (BLOCK-001 above) |
| PFDA BLOCK-002 | JWT sub claim | RESOLVED (BLOCK-002 above) |
| PFDA BLOCK-003 | notification-service ASGI | RESOLVED (BLOCK-003 above) |
| PFDA BLOCK-004 | Session v2 prefix | RESOLVED (BLOCK-005 above) |

---

## Net Frontend Blocker Count

| Phase | Hard Blockers Identified | Hard Blockers Remaining |
|---|---|---|
| PFDA | 4 | 4 (pending) |
| Phase 2.9 | +1 (OA-004 elevated to blocker) | 0 |

**All 5 hard blockers are now RESOLVED. Frontend development may begin.**
