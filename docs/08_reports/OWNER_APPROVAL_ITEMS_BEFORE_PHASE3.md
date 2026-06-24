# OWNER APPROVAL ITEMS BEFORE PHASE 3

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Source: Five-domain audit findings requiring owner decision before Frontend Authority Capture begins.

Items below require source code behavior changes, API changes, database/schema changes, auth/security changes, or architecture decisions. They cannot be fixed by documentation correction alone.

---

## OA-001: notification-service — Missing ASGI Shim (Startup Failure)

| Field | Value |
|---|---|
| **ID** | OA-001 |
| **Issue** | notification-service (port 8122) uses `BaseHTTPRequestHandler` like auth-service and checkout-service, but has no FastAPI ASGI `app` object. Manifest registers `app.main:app`. Uvicorn startup will fail with `AttributeError`. |
| **Evidence** | `backend/services/notification-service/app/main.py` — stdlib HTTPServer, no `app` variable. SERVICE_CATALOG.md "Non-Standard Services" table omits notification-service. |
| **Options** | (a) Add FastAPI ASGI shim to notification-service/app/main.py — same pattern used for auth-service and checkout-service in Task 7. (b) Update manifest to use a different startup command. |
| **Risk** | notification-service cannot start under uvicorn with current manifest entry. Email/notification delivery unavailable. |
| **Recommendation** | Option (a) — add ASGI shim. Low risk, identical to Task 7 pattern. |

---

## OA-002: branch_ids Missing from AssignmentCreateRequest

| Field | Value |
|---|---|
| **ID** | OA-002 |
| **Issue** | `USER_ROLES_AND_PERMISSIONS.md` documents `SubjectRoleAssignment` with `branch_ids: list[str] | None = None` for BRANCH scope assignments. The actual `AssignmentCreateRequest` in `rbac-service/app/schemas.py:26–36` has no `branch_ids` field. Branch-scoped role assignments cannot be created via API as currently coded. |
| **Evidence** | `backend/services/rbac-service/app/schemas.py:26–36` — `AssignmentCreateRequest` fields: `subject_type`, `subject_id`, `role_id`, `scope_type`, `scope_id`, `tenant_id`. No `branch_ids`. |
| **Options** | (a) Add `branch_ids: list[str] | None = None` to `AssignmentCreateRequest` and implement handling in rbac-service main.py. (b) Remove `branch_ids` from the permissions contract (drop BRANCH scope from planned UI). |
| **Risk** | Multi-branch role assignment (documented as a feature) is non-functional at the API level. Frontend cannot implement branch-scoped RBAC. |
| **Recommendation** | Option (a) — small schema addition, high value for multi-branch institutional use case. |

---

## OA-003: Enrollments Unique Constraint Absent from SQLite Schema

| Field | Value |
|---|---|
| **ID** | OA-003 |
| **Issue** | `core-lms-schema.md` and `DATABASE_SCHEMA.md` document a `(tenant_id, user_id, course_id)` unique constraint on enrollments. The actual `enrollments` table in `enrollment-service/app/store_db.py` has only an index on these columns, not a UNIQUE constraint. Duplicate enrollments are possible. |
| **Evidence** | `enrollment-service/app/store_db.py` — `CREATE INDEX idx_enrollments_lookup ON enrollments(tenant_id, learner_id, course_id)`. No `UNIQUE` keyword. |
| **Options** | (a) Add `UNIQUE(tenant_id, learner_id, course_id)` constraint to enrollments table + migration handling. (b) Remove unique constraint from documentation. (c) Enforce uniqueness at the service layer in enrollment-service. |
| **Risk** | Without the constraint, a user can be double-enrolled in the same course under the same tenant. Progress tracking, certification, and billing could be affected. |
| **Recommendation** | Option (a) — add the constraint. Low risk for a new SQLite deployment (no existing data to migrate). Service layer may also need upsert handling. |

---

## OA-004: service:ClassName Runtime — 3 Services Undeployable

| Field | Value |
|---|---|
| **ID** | OA-004 |
| **Issue** | capability-registry, config-service, entitlement-service are registered in the manifest with `service:CapabilityRegistryService` / `service:ConfigService` / `service:EntitlementService` format. No runtime that interprets this format was found anywhere in the repository (infrastructure/, scripts/, or elsewhere). These services cannot be deployed as HTTP services. |
| **Evidence** | Manifest entries; no loader found after searching infrastructure/service-discovery/, scripts/, all Python files. Newer HTTP implementations exist in backend/services/ but are unregistered. |
| **Options** | (a) Update manifest entries to point to `backend/services/capability-registry/app/main.py` equivalents (which are stdlib HTTP) and add ASGI shims. (b) Write or document the custom loader. (c) Remove these 3 services from the manifest if they are not needed. |
| **Risk** | 3 services are registered but unrunnable. If any other service depends on them at startup, that service will also fail. |
| **Recommendation** | Option (a) — replace manifest entries with backend/services/ versions. But confirm functionality parity first (root-layer class logic vs backend HTTP layer). |

---

## OA-005: assessment-service vs attempt-service Route Overlap

| Field | Value |
|---|---|
| **ID** | OA-005 |
| **Issue** | `assessment-service/app/main.py` registers both `/api/v1/assessments/*` AND `/api/v1/attempts/*` routes. `attempt-service` is a separate registered service (port 8103) which likely also owns `/api/v1/attempts/*`. This creates potential duplicate ownership. |
| **Evidence** | `backend/services/assessment-service/app/main.py` — 18+ endpoints across both base paths. Separate `backend/services/attempt-service/` directory exists in manifest at port 8103. |
| **Options** | (a) Confirm attempt-service owns `/api/v1/attempts/` and remove attempt routes from assessment-service. (b) Confirm assessment-service owns both and remove attempt-service from manifest. (c) Document the split: assessment-service handles attempt creation during assessment sessions; attempt-service handles standalone attempt management. |
| **Risk** | Frontend calling the wrong service for attempt operations, or two services returning inconsistent attempt state. |
| **Recommendation** | Inspect attempt-service/app/main.py to determine actual routes, then decide. |

---

## OA-006: Root services/ Classification — entitlement + subscription Active

| Field | Value |
|---|---|
| **ID** | OA-006 |
| **Issue** | Root `services/` layer (20 dirs) is partially active. `services/entitlement-service/` is imported by payment-service (guarded). `services/subscription-service/` is imported by tenant-service (guarded). Root `shared/control_plane.py` and `shared/utils/entitlement.py` are imported by 5 backend services. The other 18 root service dirs appear inactive. |
| **Evidence** | Import analysis from repo hygiene audit: `from services.entitlement_service.service import EntitlementService` in payment-service; `from services.subscription_service import SubscriptionService` in tenant-service. |
| **Options** | (a) Mark entitlement-service and subscription-service as ACTIVE (cannot archive); mark the other 18 as LEGACY. (b) Migrate the active logic into backend/services/ equivalents to eliminate root-layer dependency. |
| **Risk** | Archiving entitlement-service or subscription-service dirs would break payment-service and tenant-service at import time. |
| **Recommendation** | Option (a) short-term. Option (b) for long-term cleanup. Add LEGACY banners to the 18 inactive dirs. |

---

## OA-007: Two Competing EventEnvelope Definitions

| Field | Value |
|---|---|
| **ID** | OA-007 |
| **Issue** | Two EventEnvelope class definitions exist: (1) `backend/services/shared/events/envelope.py` — `EventEnvelope` dataclass with 10 fields (canonical anchor's 7 + topic, producer_service, schema_version). (2) `backend/services/course-service/app/schemas.py:213–220` — local `EventEnvelope` Pydantic model with exactly 7 fields matching the canonical anchor. These produce different envelope shapes. |
| **Evidence** | Both files confirmed. |
| **Options** | (a) Remove course-service's local EventEnvelope and import from shared. (b) Accept both — course-service uses the 7-field anchor shape externally; shared bus uses 10-field internally. |
| **Risk** | If course-service publishes events using its local 7-field definition, those events are missing `topic`, `producer_service`, `schema_version` compared to what subscribers may expect. |
| **Recommendation** | Option (a) — consolidate on shared/events/envelope.py. |

---

## OA-008: integrations/payment/ vs integrations/payments/ Overlap

| Field | Value |
|---|---|
| **ID** | OA-008 |
| **Issue** | Two directories at root integrations level: `integrations/payment/` (8 files) and `integrations/payments/` (26 files). payment-service imports from `integrations.payments` (plural). The singular directory's purpose and import status are unverified. |
| **Evidence** | `backend/services/payment-service/` imports from `integrations.payments` (plural confirmed active). `integrations/payment/` (singular) — no confirmed import found. |
| **Options** | (a) Verify singular `payment/` has no importers, then archive/remove it. (b) Merge into `payments/`. |
| **Risk** | Accidental deletion of `payment/` if it has undiscovered consumers. |
| **Recommendation** | Grep for `from integrations.payment import` — if zero results, archive singular dir. |

---

## OA-009: session-service v2 API Prefix — Contract Gap

| Field | Value |
|---|---|
| **ID** | OA-009 |
| **Issue** | session-service uses `/api/v2/sessions` as base path. All other services use `/api/v1/`. This versioning decision is not documented in any contract, API_CONTRACT.md, or versioning strategy document. Frontend may incorrectly construct session-service URLs with `/v1/`. |
| **Evidence** | `backend/services/session-service/app/main.py` — FastAPI with prefix `/api/v2/sessions`. `docs/architecture/api-versioning-strategy.md` — does not mention session-service as an exception. |
| **Options** | (a) Document the v2 prefix as intentional in API_CONTRACT.md and versioning strategy (if session-service has a breaking API revision history). (b) Standardize to v1 (breaking change to any existing session-service consumers). |
| **Risk** | Any frontend or service-to-service call using `/api/v1/sessions/` will 404. |
| **Recommendation** | Option (a) — document the v2 prefix as-is. It's likely intentional. |

---

## OA-010: docs/qc/ Python Scripts — Move to validation/

| Field | Value |
|---|---|
| **ID** | OA-010 |
| **Issue** | 11 Python scripts (`.py`) remain in `docs/qc/`. Per DOCUMENTATION_PLACEMENT_AUDIT.md DP-001 and REPOSITORY_RESTRUCTURING_PLAN.md P4-MOVE-001, they should be in `validation/`. The move requires verifying no CI/CD or documentation references depend on their `docs/qc/` path. |
| **Evidence** | 11 .py files confirmed present in docs/qc/. validation/ directory exists. |
| **Options** | (a) Move files to validation/, update any path references. (b) Leave in docs/qc/ if paths are load-bearing for existing tooling. |
| **Risk** | Low — scripts are standalone; docs/ is not a conventional path for executable code. |
| **Recommendation** | Option (a). Owner approval needed only to confirm no undocumented tooling depends on docs/qc/ path. |

---

---

## OA-011: Dockerfiles and CI/CD Exist Despite Stated Constraint

| Field | Value |
|---|---|
| **ID** | OA-011 |
| **Issue** | `AI_OPERATING_CONTEXT.md` includes an operational constraint: "No Dockerfiles or CI/CD in repository." However, `infrastructure/deployment/docker/Dockerfile.python`, `Dockerfile.node`, `infrastructure/deployment/docker-compose.yml`, `infrastructure/observability/docker-compose.yml`, and `infrastructure/deployment/cicd/deploy-backend.yml` all exist in the repository. |
| **Options** | (a) Remove the files from the repository. (b) Update AI_OPERATING_CONTEXT.md to reflect that these files exist (constraint was aspirational or pre-dates the files). |
| **Risk** | Low — files are in infrastructure/ not in service code. They don't affect runtime behavior. |
| **Recommendation** | Option (b) — update the constraint statement to "Do not add new Dockerfiles or CI/CD files." The existing ones were presumably created intentionally. |

---

## OA-012: analytics-ingestion-service vs event-ingestion-service Name Mismatch

| Field | Value |
|---|---|
| **ID** | OA-012 |
| **Issue** | Event documentation, `event_topics.json`, and possibly the service manifest reference `analytics-ingestion-service` as the producer for analytics domain topics. The actual directory in `backend/services/` is `event-ingestion-service/`. Either the directory was renamed after the docs were written, or there's a manifest entry mismatch. |
| **Options** | (a) Verify manifest entry name — if manifest says `analytics-ingestion-service`, the service directory should match. Rename one or the other. (b) If both names coexist, determine which is authoritative. |
| **Risk** | Medium — service cannot start if manifest path doesn't match directory name. |
| **Recommendation** | Verify service-manifest.json entry for this service, then align doc/directory accordingly. |

---

## OA-013: event_topics.json Topic Names vs Code Topic Strings

| Field | Value |
|---|---|
| **ID** | OA-013 |
| **Issue** | `event_topics.json` documents canonical topic names as `lms.<domain>.<event>.v1`. Actual code uses inconsistent short names: auth-service publishes `"auth.login.failed"`, attempt-service publishes `"assessment.submission"`, payment-service publishes `"payment.success"`. enrollment-service dual-subscribes `"lms.enrollment.status_changed.v1"` AND `"enrollment.completed"` (resilience pattern). |
| **Options** | (a) Standardize all code to use canonical `lms.*` names. (b) Accept the aliases and document the dual-name pattern in event_topics.json. (c) Define alias mapping in event_bus_config.json. |
| **Risk** | Publishers and subscribers may use different names — events are silently dropped. The enrollment dual-subscribe pattern suggests this problem has already been encountered. |
| **Recommendation** | Option (a) for new events; Option (b) for existing aliases with explicit alias documentation. |

---

## Summary

**Phase 2.9 Status: ALL 13 ITEMS RESOLVED — 2026-06-23**

| ID | Topic | Code Change? | Priority | Phase 2.9 Status |
|---|---|---|---|---|
| OA-001 | notification-service ASGI shim | Yes — same as Task 7 pattern | HIGH | ✅ FIXED |
| OA-002 | branch_ids in AssignmentCreateRequest | Yes — API schema change | MEDIUM | ✅ FIXED |
| OA-003 | Enrollments unique constraint | No gap — service layer is correct | MEDIUM | ✅ CLOSED (not a gap) |
| OA-004 | service:ClassName runtime | Yes — manifest + code | HIGH | ✅ FIXED |
| OA-005 | assessment/attempt route overlap | Not a conflict — intentional alias | HIGH | ✅ CLOSED (code evidence) |
| OA-006 | Root services/ classification | Doc update | MEDIUM | ✅ DOCUMENTED |
| OA-007 | Competing EventEnvelope definitions | Code consolidation | MEDIUM | ✅ FIXED |
| OA-008 | integrations/payment vs payments | Both active — not a conflict | LOW | ✅ CLOSED (both active) |
| OA-009 | session-service v2 prefix | Doc update | MEDIUM | ✅ DOCUMENTED |
| OA-010 | docs/qc/ Python scripts move | File move | LOW | ✅ DONE |
| OA-011 | Dockerfiles/CI/CD constraint statement | Doc update | LOW | ✅ DOCUMENTED |
| OA-012 | analytics-ingestion vs event-ingestion name | Doc fix | MEDIUM | ✅ DOCUMENTED |
| OA-013 | event_topics.json canonical names vs code | Pattern documented | MEDIUM | ✅ DOCUMENTED |

See REPOSITORY_DETERMINABILITY_REVIEW.md and APPROVAL_ELIMINATION_REPORT.md for full evidence record.
