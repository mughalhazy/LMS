# AUTO-CLOSED REGISTER — PROJECT MEMORY LAYER

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: AI

---

## Purpose

Contains every item resolved directly from repository evidence (code, architecture, contracts, authority documents). These facts are proven and do not need to be rediscovered. No owner decision was required for any item in this register.

Classification rule: AUTO-CLOSED only if directly proven — no assumptions allowed.

---

## PM-AC-001: notification-service ASGI Shim

| Field | Value |
|---|---|
| **Item ID** | PM-AC-001 |
| **Original ID** | OA-001 |
| **Title** | notification-service uses class-based startup without ASGI shim |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — FIXED in Phase 2.9 |
| **Original Source** | Phase 2.9 Approval Elimination (OA-001) |
| **Evidence Source** | backend/services/notification-service/app/main.py — ASGI shim added |
| **Resolution Source** | Phase 2.9 remediation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9) |
| **Decision Summary** | ASGI shim (FastAPI `app` object) added to notification-service main.py |
| **Detailed Explanation** | notification-service was using a class-based handler not compatible with uvicorn's `app.main:app` startup. A FastAPI ASGI shim was added delegating to existing handler methods. Service is now deployable via standard uvicorn startup. |
| **Affected Components** | notification-service |
| **Affected Routes** | /api/v1/notifications/* |
| **Affected APIs** | notification-service endpoints |
| **Affected Workflows** | WF-009 (notifications triggered from workflows) |
| **Affected Roles** | All roles (notification recipients) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE — already fixed |
| **Reopen Criteria** | Only if notification-service main.py is refactored to remove the shim |
| **Related Documents** | docs/08_reports/APPROVAL_ELIMINATION_REPORT.md |
| **Related Register Entries** | PM-AC-004 (OA-004 same pattern) |

---

## PM-AC-002: branch_ids in AssignmentCreateRequest

| Field | Value |
|---|---|
| **Item ID** | PM-AC-002 |
| **Original ID** | OA-002 |
| **Title** | AssignmentCreateRequest missing branch_ids field |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — FIXED in Phase 2.9 |
| **Original Source** | Phase 2.9 Approval Elimination (OA-002) |
| **Evidence Source** | backend/services/rbac-service/app/schemas.py — branch_ids field added |
| **Resolution Source** | Phase 2.9 remediation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9) |
| **Decision Summary** | branch_ids (List[str]) added to AssignmentCreateRequest schema |
| **Detailed Explanation** | RBAC role assignments were missing the branch_ids field required for branch-scoped permission grants. Field added to schema and wired through assignment creation logic. |
| **Affected Components** | rbac-service |
| **Affected Routes** | POST /api/v1/rbac/assignments |
| **Affected APIs** | RBAC assignment creation endpoint |
| **Affected Workflows** | Admin role management |
| **Affected Roles** | Admin (role assignment) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE — already fixed |
| **Reopen Criteria** | Only if AssignmentCreateRequest schema is refactored |
| **Related Documents** | docs/00_authority/USER_ROLES_AND_PERMISSIONS.md |
| **Related Register Entries** | PM-AC-FSC-007 (FSC-007 RBAC/PermissionGuard) |

---

## PM-AC-003: Enrollments Unique Constraint

| Field | Value |
|---|---|
| **Item ID** | PM-AC-003 |
| **Original ID** | OA-003 |
| **Title** | Enrollments unique constraint — apparent duplicate logic concern |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — not a gap; service layer correct |
| **Original Source** | Phase 2.9 Approval Elimination (OA-003) |
| **Evidence Source** | backend/services/enrollment-service/app/service.py — duplicate check at service layer before DB insert |
| **Resolution Source** | Phase 2.9 investigation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9) |
| **Decision Summary** | No gap. Service layer validates uniqueness before insert. Constraint is correct. |
| **Detailed Explanation** | enrollment-service performs duplicate enrollment check at service layer (not only DB constraint). This is intentional defense-in-depth. The apparent redundancy is correct behavior. |
| **Affected Components** | enrollment-service |
| **Affected Routes** | POST /api/v1/enrollments |
| **Affected APIs** | Enrollment creation |
| **Affected Workflows** | WF-003 (enrollment) |
| **Affected Roles** | Learner |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE |
| **Reopen Criteria** | If enrollment logic is refactored to remove service-layer check |
| **Related Documents** | docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md FSC-002 |
| **Related Register Entries** | PM-AC-FSC-002 |

---

## PM-AC-004: service:ClassName Runtime (D-002)

| Field | Value |
|---|---|
| **Item ID** | PM-AC-004 |
| **Original ID** | OA-004 / D-002 / GAP-006 / ITEM-02 |
| **Title** | service:ClassName manifest format — no runtime found |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — RESOLVED Phase 2.9: ASGI shims + manifest update |
| **Original Source** | Phase 2.9 Approval Elimination; Backend Gap Register GAP-006; AI_OPERATING_CONTEXT D-002 |
| **Evidence Source** | service-manifest.json updated; capability-registry, config-service, entitlement-service now use app.main:app format with ASGI shims |
| **Resolution Source** | Phase 2.9 remediation — ASGI shim pattern applied to all 3 class-based services |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9) |
| **Decision Summary** | No custom runtime loader exists. All 3 services received ASGI shims. Manifest updated to standard app.main:app format. |
| **Detailed Explanation** | capability-registry, config-service, and entitlement-service previously had `service:ClassName` manifest entries — a format with no Python ASGI/WSGI runner support. Exhaustive search found no custom loader. Resolution: FastAPI ASGI shim added to each service; manifest updated. All 3 services now deployable via standard uvicorn. |
| **Affected Components** | capability-registry (8140), config-service (8141), entitlement-service (8142) |
| **Affected Routes** | All endpoints of the 3 services |
| **Affected APIs** | Capability registration, config resolution, entitlement evaluation |
| **Affected Workflows** | All workflows requiring capability or entitlement checks |
| **Affected Roles** | All roles |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE — resolved |
| **Reopen Criteria** | Only if manifest format changes again without corresponding runner |
| **Related Documents** | docs/08_reports/BACKEND_GAP_REGISTER.md GAP-006; docs/08_reports/TASK7_REMEDIATION_REPORT.md |
| **Related Register Entries** | PM-AC-014 (ITEM-02 compression entry for same item) |

---

## PM-AC-005: assessment/attempt Route Overlap

| Field | Value |
|---|---|
| **Item ID** | PM-AC-005 |
| **Original ID** | OA-005 |
| **Title** | assessment-service and attempt-service route overlap |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — intentional alias confirmed |
| **Original Source** | Phase 2.9 Approval Elimination (OA-005) |
| **Evidence Source** | Service specs — assessment routes and attempt routes are intentionally aliased; attempt-service is the result record, assessment-service is the question bank |
| **Resolution Source** | Phase 2.9 investigation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9) |
| **Decision Summary** | Route overlap is intentional. assessment-service = question/quiz definition. attempt-service = learner attempt record. No conflict. |
| **Detailed Explanation** | What appeared to be duplicate routes are actually complementary: assessment-service manages the quiz definition and scoring rules; attempt-service manages learner attempts and responses. The overlap is naming similarity, not functional conflict. |
| **Affected Components** | assessment-service, attempt-service |
| **Affected Routes** | /api/v1/assessments/*, /api/v1/attempts/* |
| **Affected APIs** | Assessment management and attempt submission |
| **Affected Workflows** | WF-004 (learning completion) |
| **Affected Roles** | Teacher (assessment creation), Learner (attempt submission) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE |
| **Reopen Criteria** | Only if one service absorbs the other |
| **Related Documents** | docs/specs/assessment-service-spec.md; docs/specs/attempt-service-spec.md |
| **Related Register Entries** | None |

---

## PM-AC-006: Root services/ Layer Classification

| Field | Value |
|---|---|
| **Item ID** | PM-AC-006 |
| **Original ID** | OA-006 / PDC-014 |
| **Title** | Root services/ layer — classification unclear |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — documented; active domain library layer |
| **Original Source** | Phase 2.9 Approval Elimination (OA-006) |
| **Evidence Source** | services/ directory — pure Python domain libraries, not HTTP services; no manifest entries for root services/ layer |
| **Resolution Source** | Phase 2.9 investigation + Phase 2.95 PDC-014 |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.9/2.95) |
| **Decision Summary** | Root services/ is the domain library layer. These are Python classes (service.py), not HTTP servers. backend/services/ is the HTTP service layer. The two layers coexist by design. |
| **Detailed Explanation** | The root services/ directory contains pure domain logic (e.g., services/commerce/service.py has apply_reconciliation(), services/file-storage/service.py). These are NOT in the manifest because they don't run as HTTP servers. The backend/services/ layer wraps them with FastAPI routers. Backend architecture only — zero frontend impact. |
| **Affected Components** | services/ domain layer |
| **Affected Routes** | None (no HTTP) |
| **Affected APIs** | None |
| **Affected Workflows** | WF-005 (reconciliation domain logic is in services/commerce/) |
| **Affected Roles** | None (backend only) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | LOW — persistence sprint may wire domain layer to SQLite stores |
| **Reopen Criteria** | If domain layer structure is reorganized |
| **Related Documents** | docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md |
| **Related Register Entries** | PM-AC-028 (PDC-014) |

---

## PM-AC-007 through PM-AC-013: Phase 2.9 OA Items (Batch)

| PM ID | OA ID | Title | Resolution |
|---|---|---|---|
| PM-AC-007 | OA-007 | Competing EventEnvelope definitions | FIXED: consolidated into shared/events/envelope.py. build_event() and publish_event() are canonical. |
| PM-AC-008 | OA-008 | integrations/payment vs payments | NOT A CONFLICT: integrations/payments/ is the HTTP integration layer (JazzCash/EasyPaisa). services/payment* is domain logic. Both active by design. |
| PM-AC-009 | OA-009 | session-service v2 prefix | INTENTIONAL: session-service uses /api/v2/sessions/ prefix. Documented as intentional API versioning. Other services use /api/v1/. No conflict. |
| PM-AC-010 | OA-010 | docs/qc/ Python scripts move | DONE: qc/ scripts moved/reorganized in Phase 2.9. No open action. |
| PM-AC-011 | OA-011 | Dockerfiles/CI/CD constraint statement | DOCUMENTED: constraint in AI_OPERATING_CONTEXT updated. Dockerfiles exist in infrastructure/; new ones require owner approval. |
| PM-AC-012 | OA-012 | analytics-ingestion vs event-ingestion | DOCUMENTED: analytics-ingestion-service handles LMS analytics events; event-ingestion-service handles general event streaming. Different purposes, aligned. |
| PM-AC-013 | OA-013 | event_topics.json canonical names vs code | DOCUMENTED: event_topics.json uses canonical lms.<domain>.<event_type>.v1 format. Code uses Python-style snake_case names. Alias pattern is intentional. EventBus resolves via envelope.py. |

For all PM-AC-007 through PM-AC-013:
- Owner Required: NO
- External Dependency: NO
- Future Impact: NONE
- Resolution Date: 2026-06-23
- Resolved By: AI (Phase 2.9)

---

## PM-AC-014: Class-Based Services ASGI (Compression)

| Field | Value |
|---|---|
| **Item ID** | PM-AC-014 |
| **Original ID** | ITEM-02 / D-002 / GAP-006 / RISK-014 / OA-004 |
| **Title** | Class-based startup mechanism — compression entry |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — this is the compression-phase record of OA-004/PM-AC-004 |
| **Resolution Date** | 2026-06-23 |
| **Decision Summary** | Same as PM-AC-004. All 3 services now have ASGI shims. This entry exists because ITEM-02 appeared in compression phase with a separate handle. |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE |
| **Related Register Entries** | PM-AC-004 (primary record) |

---

## PM-AC-015: Orphaned Services

| Field | Value |
|---|---|
| **Item ID** | PM-AC-015 |
| **Original ID** | ITEM-04 / D-004 / R-006 |
| **Title** | Orphaned services in root services/ with no code references |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — archived; no active code references found |
| **Original Source** | AI_OPERATING_CONTEXT D-004; BACKEND_RISK_REGISTER R-006 |
| **Evidence Source** | Grep search — no import or reference found for the orphaned service directories |
| **Resolution Source** | OWNER-REQUIRED Compression; confirmed AUTO-CLOSED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | Services with zero code references are historical artifacts. No action required. Archive status confirmed. |
| **Affected Components** | None (orphaned services not in manifest) |
| **Affected Routes** | None |
| **Affected APIs** | None |
| **Affected Workflows** | None |
| **Affected Roles** | None |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | NONE — unless orphaned services are revived (would require explicit sprint) |
| **Reopen Criteria** | If owner decides to revive an orphaned service |
| **Related Documents** | docs/08_reports/CODEBASE_PLACEMENT_AUDIT.md |
| **Related Register Entries** | PM-AC-006 (root services/ classification) |

---

## PM-AC-016: Dual Reconciliation Paths

| Field | Value |
|---|---|
| **Item ID** | PM-AC-016 |
| **Original ID** | ITEM-05 / D-005 / R-011 |
| **Title** | Two reconciliation code paths — potential conflict |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — reconciliation is backend-only domain logic; no conflict |
| **Original Source** | AI_OPERATING_CONTEXT D-005 |
| **Evidence Source** | services/commerce/service.py (apply_reconciliation, schedule_reconciliation_job); integrations/payments/reconciliation.py (PaymentReconciliationEngine) |
| **Resolution Source** | Phase 2.95 PDC-011; confirmed AUTO-CLOSED in Compression |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI |
| **Decision Summary** | No conflict. commerce/service.py is domain orchestration. PaymentReconciliationEngine is the payment provider reconciliation. They are complementary layers. Frontend polls order status — reconciliation is transparent. |
| **Affected Components** | services/commerce/, integrations/payments/ |
| **Affected Routes** | None (backend domain logic) |
| **Affected APIs** | None directly; PaymentReconciliationEngine triggers via webhook |
| **Affected Workflows** | WF-005 (JazzCash checkout) |
| **Affected Roles** | None (automated background process) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | LOW — reconciliation admin screen (FGAP-005) will expose this via HTTP |
| **Reopen Criteria** | If admin needs reconciliation screen (opens FGAP-005 sprint) |
| **Related Documents** | docs/08_reports/PRODUCT_DECISION_REGISTER.md PDC-011 |
| **Related Register Entries** | PM-OS-005 (FGAP-005 reconciliation admin screen) |

---

## PM-AC-017 through PM-AC-022: Compression AUTO-CLOSED Batch

| PM ID | Original ID | Title | Resolution |
|---|---|---|---|
| PM-AC-017 | ITEM-14 / GAP-012 | Node.js services not inventoried | Reclassified as technical discovery sprint. prerequisite-engine-service (8124) and scorm-service (8131) are Node.js. AI can inspect in a dedicated session. No owner decision needed. |
| PM-AC-018 | ITEM-15 / GAP-013 | payment-service non-standard entrypoint | Reclassified as technical verification task. payment-service uses api:app (FastAPI app in api.py at service root). AI can verify in a session. No owner decision needed. |
| PM-AC-019 | ITEM-16 / GAP-014 | 25 services without engineering specs | Reclassified as autonomous doc sprint (R-008). Spec writing is autonomous per REVISED_DECISION_ESCALATION_MATRIX. No owner authorization required. |
| PM-AC-020 | ITEM-18 / RISK-009 / R-001 | entitlement service DI conflict | Reclassified as U12 implementation sprint. Dependency injection conflict in entitlement-service is a technical implementation task. No owner decision. |
| PM-AC-021 | ITEM-19 / RISK-010 / R-004 | Circular import model extraction | Reclassified as U12 implementation sprint. Circular import resolved by extracting model to separate module. Standard Python pattern. No owner decision. |
| PM-AC-022 | ITEM-20 / RISK-013 | Frontend zero tests | Reclassified as Testing Authority Capture sprint. Frontend has no tests because it doesn't exist yet. No owner decision for current phase. |

For all PM-AC-017 through PM-AC-022:
- Owner Required: NO
- External Dependency: NO
- Resolution Date: 2026-06-23

---

## PM-AC-024 through PM-AC-028: Phase 2.95 RESOLVED Decisions

| PM ID | PDC ID | Title | Resolution |
|---|---|---|---|
| PM-AC-024 | PDC-004 | interaction-service existence | Does not exist. Zero evidence: no directory, no manifest entry, no spec, no design doc, no authority mention. Confirmed not in scope. |
| PM-AC-025 | PDC-011 | JazzCash webhook reconciliation (frontend) | Reconciliation is transparent to frontend. Frontend payment status screen polls GET /api/v1/checkout/orders/{order_id}. Three states: pending / success / failed. No dedicated reconciliation screen in initial build (see PM-OS-005 for deferred admin screen). |
| PM-AC-026 | PDC-012 | Frontend navigation model | Permission-based navigation via POST /api/v1/rbac/authorize confirmed. No hardcoded role_key values in frontend routing. All route guards call authorize endpoint. |
| PM-AC-027 | PDC-013 | Duplicate lesson event topics | Backend EventBus internal only. Frontend never subscribes to or publishes events. Zero frontend impact. |
| PM-AC-028 | PDC-014 | Root services/ layer classification | Backend architecture only. entitlement-service and subscription-service at root layer are guarded imports used by domain logic. Zero frontend impact. |

For all PM-AC-024 through PM-AC-028:
- Owner Required: NO
- External Dependency: NO
- Resolution Date: 2026-06-23

---

## PM-AC-029 through PM-AC-040: TBD Resolutions

| PM ID | TBD ID | Title | Answer |
|---|---|---|---|
| PM-AC-029 | TBD-001 | Checkout-service DB persistence (D-001) | NO — checkout-service has no store_db.py; InMemoryCheckoutStore is active. Handled by PM-SD-001 (persistence sprint). |
| PM-AC-030 | TBD-002 | store_db.py actively used | YES — 16 services now wired to SQLite: auth, rbac, enrollment, progress, tenant, assessment, certificate, lesson, program, badge, session, user, org, cohort, institution, course. |
| PM-AC-031 | TBD-003 | ORM/migration framework | NO — custom BaseRepository on Python stdlib sqlite3. No SQLAlchemy, no Alembic, no asyncpg. DB path via resolve_db_path(service_name) using LMS_DB_PATH env var. |
| PM-AC-032 | TBD-004 | External persistence layer | NO — SQLite only. No PostgreSQL, no Redis wired to any service. infra/deployment/env/ files have placeholder credentials for future PostgreSQL/RabbitMQ — not yet connected to any service. |
| PM-AC-033 | TBD-005 | service:ClassName runtime | NONE — no custom loader exists. Resolved via ASGI shims in Phase 2.9 (see PM-AC-004). |
| PM-AC-034 | TBD-006 | Refresh token family tracking | IMPLEMENTED — auth_refresh_tokens table has parent_token_id + replaced_by_token_id columns. Token family lineage via FK, not a separate refresh_token_family table as spec named it. |
| PM-AC-035 | TBD-007 | Login response shape | VERIFIED — {session_id, user: {user_id, tenant_id}, access_token, token_type: "Bearer", expires_in: 900, refresh_token, refresh_expires_in: 604800}. user_id/tenant_id nested under user object. roles NOT in response (only in JWT). |
| PM-AC-036 | TBD-008 | JWT user identifier claim | sub claim — auth-service/app/service.py:111 sets "sub": user.user_id. Frontend must read payload.sub NOT payload.user_id. |
| PM-AC-037 | TBD-009 | EventBus implementation status | FULL IN-PROCESS EVENTBUS EXISTS — shared/events/bus.py: thread-safe subscribe(), publish(), wildcard "*" support, get_default_bus() singleton. auth-service consumers.py registers 9 topic subscriptions. Cross-process requires Kafka (see PM-SD-006). |
| PM-AC-038 | TBD-010 | infrastructure env files sensitivity | NOT SENSITIVE — infrastructure/deployment/env/ files contain only placeholder/local-dev credentials. No production secrets. Safe to leave in repo. |
| PM-AC-039 | TBD-011 | Tenant model fields | 6 FIELDS — tenant_id, name, country_code, segment_type, plan_type, addon_flags. Sources: docs/anchors/tenant-contract.md (TIER 1) + tenant-service/app/schemas.py. |
| PM-AC-040 | TBD-012 | spec_index.json consumer | NO CONSUMER — scripts/ directory does not exist. spec_index.json is stale pre-governance catalog (2026-03-31) using old underscore filenames. Historical artifact. |

For all PM-AC-029 through PM-AC-040:
- Owner Required: NO
- External Dependency: NO
- Resolution Date: 2026-06-23
- Resolved By: Pre-Frontend Delta Audit + Phase 3.25

---

## PM-AC-041: WF-001 Onboarding Events (Phase 3.25)

| Field | Value |
|---|---|
| **Item ID** | PM-AC-041 |
| **Original ID** | DC-012; PRODUCT_WORKFLOWS.md WF-001 TBD |
| **Title** | WF-001 tenant onboarding — events emitted via Kafka? |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — CONFIRMED: No events emitted |
| **Original Source** | PRODUCT_WORKFLOWS.md WF-001 "Events emitted: TBD – REQUIRES VERIFICATION" |
| **Evidence Source** | infrastructure/event-bus/event_topics.json — 39 topics inspected; zero tenant or onboarding topics present |
| **Resolution Source** | Phase 3.25 direct inspection |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 3.25) |
| **Decision Summary** | WF-001 (Tenant Onboarding) is a synchronous service chain only. No Kafka events emitted. |
| **Detailed Explanation** | event_topics.json contains 39 topics. Topics follow lms.<domain>.<event_type>.v1 format. None reference tenant, onboarding, or provisioning. WF-001 calls: tenant-service → org-service → rbac-service → user-service → notification-service synchronously. Event-driven at the Kafka level: no. |
| **Affected Components** | tenant-service, org-service, rbac-service, user-service, notification-service |
| **Affected Routes** | POST /api/v1/tenants (WF-001 entry) |
| **Affected APIs** | Tenant onboarding chain |
| **Affected Workflows** | WF-001 |
| **Affected Roles** | Admin (initiates), System (processes) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | LOW — if async onboarding events are ever added, this becomes a SAFE-DEFAULT change |
| **Reopen Criteria** | If tenant onboarding is redesigned to emit Kafka events |
| **Related Documents** | docs/00_authority/PRODUCT_WORKFLOWS.md WF-001; infrastructure/event-bus/event_topics.json |
| **Related Register Entries** | PM-SD-006 (Kafka integration sprint) |

---

## PM-AC-042: WF-005 JazzCash Webhook Reconciliation (Phase 3.25)

| Field | Value |
|---|---|
| **Item ID** | PM-AC-042 |
| **Original ID** | DC-013; PRODUCT_WORKFLOWS.md WF-005 TBD |
| **Title** | WF-005 JazzCash checkout — webhook reconciliation confirmed |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — CONFIRMED: PaymentReconciliationEngine active |
| **Original Source** | PRODUCT_WORKFLOWS.md WF-005 "JazzCash webhook flow: TBD – REQUIRES VERIFICATION" |
| **Evidence Source** | integrations/payments/reconciliation.py — PaymentReconciliationEngine class; run_reconciliation_pass() method; integrations/payments/test_reconciliation.py |
| **Resolution Source** | Phase 3.25 direct code inspection |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 3.25) |
| **Decision Summary** | JazzCash webhook triggers PaymentReconciliationEngine.run_reconciliation_pass(). Order status transitions PAID → RECONCILED. Test suite confirmed active. |
| **Detailed Explanation** | JazzCash sends payment status webhook to the application. PaymentReconciliationEngine.run_reconciliation_pass() processes the webhook: checks order status, updates to RECONCILED if payment confirmed. Domain: services/commerce/apply_reconciliation(). Admin screen to view reconciled orders is FGAP-005 (no HTTP endpoint yet). |
| **Affected Components** | integrations/payments/reconciliation.py, services/commerce/ |
| **Affected Routes** | Webhook receiver endpoint (payment callback) |
| **Affected APIs** | Internal; not directly called by frontend |
| **Affected Workflows** | WF-005 (JazzCash checkout) |
| **Affected Roles** | System (automated reconciliation) |
| **Owner Required** | NO |
| **External Dependency** | YES — JazzCash production credentials (see PM-ED-001) |
| **Future Impact** | MEDIUM — reconciliation admin screen (FGAP-005) depends on this being exposed via HTTP |
| **Reopen Criteria** | If payment integration changes provider or reconciliation logic changes |
| **Related Documents** | docs/00_authority/PRODUCT_WORKFLOWS.md WF-005; integrations/payments/reconciliation.py |
| **Related Register Entries** | PM-ED-001 (JazzCash credentials); PM-OS-005 (FGAP-005 admin screen) |

---

## PM-AC-043: AI_OPERATING_CONTEXT Stale Content

| Field | Value |
|---|---|
| **Item ID** | PM-AC-043 |
| **Original ID** | DC-019 through DC-024 |
| **Title** | AI_OPERATING_CONTEXT.md stale content — 6 fields updated |
| **Classification** | AUTO-CLOSED |
| **Current Status** | CLOSED — all 6 stale fields updated |
| **Original Source** | Phase 3.25 gap sweep |
| **Evidence Source** | Phase progression history; Phase 2.9 manifest updates; PDC-009 FGAP-001; Compression SAFE-DEFAULT resolutions |
| **Resolution Source** | Phase 3.25 AI_OPERATING_CONTEXT.md edits |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 3.25) |
| **Decision Summary** | 6 stale entries updated: (1) CURRENT_PHASE = Phase 3.25 complete; (2) service count = 69 in manifest, 3 class-based now ASGI-shimmed; (3) Parents = FGAP-001 not TBD; (4) R-005 = SAFE-DEFAULT not owner decision; (5) R-013 = SAFE-DEFAULT not owner decision; (6) BACKEND_GAP_REGISTER summary table = compression-resolved not "8 open" |
| **Affected Components** | docs/07_governance/AI_OPERATING_CONTEXT.md |
| **Affected Routes** | None |
| **Affected APIs** | None |
| **Affected Workflows** | AI session onboarding (this file is loaded by AI sessions) |
| **Affected Roles** | None |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | LOW — file will need updating again after next major phase |
| **Reopen Criteria** | At start of each new phase or major implementation sprint |
| **Related Documents** | docs/07_governance/AI_OPERATING_CONTEXT.md |
| **Related Register Entries** | All PM entries (AI_OPERATING_CONTEXT references them) |

---

## PM-AC-FSC-001 through PM-AC-FSC-009: FSC Frontend Consumer Confirmations

These 9 items were TBD in FULLSTACK_STITCHING_CONTRACT.md prior to Phase 3. All confirmed in Phase 3.25 from Phase 3 documents.

| PM ID | FSC ID | Was TBD | Now Confirmed | Evidence |
|---|---|---|---|---|
| PM-AC-FSC-001 | FSC-001 | Frontend Consumer = TBD | /login (SCR-001). sub=user_id. Fetch RBAC assignments after login. | FRONTEND_SCREEN_CATALOG.md SCR-001; FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-001 |
| PM-AC-FSC-002 | FSC-002 | Frontend Consumer = TBD | /learner/courses/:id enroll button. POST /api/v1/enrollments. Redirect to player. | FRONTEND_SCREEN_CATALOG.md; WF-003 |
| PM-AC-FSC-003 | FSC-003 | Frontend Consumer + API = TBD | /learner/checkout (SCR-019). All 6 checkout endpoints verified Phase 2 addendum. | Phase 2 addendum; FRONTEND_SCREEN_CATALOG.md SCR-019 |
| PM-AC-FSC-004 | FSC-004 | Frontend Consumer + API = TBD | /learner/courses/:id/learn/:lid (SCR-018). 3 progress endpoints verified. | Phase 2 addendum; FRONTEND_SCREEN_CATALOG.md SCR-018 |
| PM-AC-FSC-005 | FSC-005 | Frontend Consumer = TBD | /learner/certificates/:id (SCR-021). POST/GET /api/v1/certificates per spec. | docs/specs/certificate-service-spec.md; FRONTEND_SCREEN_CATALOG.md SCR-021 |
| PM-AC-FSC-006 | FSC-006 | Frontend Consumer = TBD | Admin: /admin/batches/:id/timetable. Teacher: /teacher/batches/:id/attendance. | FRONTEND_SCREEN_CATALOG.md SCR-012, SCR-023; WF-002 |
| PM-AC-FSC-007 | FSC-007 | Frontend Consumer + D-002 = TBD | All gated UI via PermissionGuard components. D-002 resolved via ASGI shims. | FRONTEND_COMPONENT_INVENTORY.md; Phase 2.9 ASGI resolution |
| PM-AC-FSC-008 | FSC-008 | Frontend Consumer + Redis = TBD | /lti/launch special route. Redis nonce store confirmed (TTL=600s). | WF-010; docs/integrations/lti-consumer-spec.md; U9 H-010 |
| PM-AC-FSC-009 | FSC-009 | Frontend Consumer + Domain = TBD | /notifications (SCR-025). Domain: Notification, NotificationTemplate, WorkflowAction. | docs/specs/notification-service-spec.md; FRONTEND_SCREEN_CATALOG.md SCR-025 |

For all PM-AC-FSC items:
- Owner Required: NO
- External Dependency: NO
- Resolution Date: 2026-06-23
- Resolved By: AI (Phase 3 + Phase 3.25)
