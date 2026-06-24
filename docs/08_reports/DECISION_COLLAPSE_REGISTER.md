# DECISION COLLAPSE REGISTER

Status: Complete
Date: 2026-06-23
Phase: Phase 3.25 — Autonomous Gap Elimination and Determinism Enforcement
Owner: AI

---

## Purpose

Canonical register of every decision that was collapsed (resolved autonomously from repository evidence) during Phase 3.25. Each entry documents the item, the evidence used to resolve it, and the classification applied.

This document is additive to:
- RESIDUAL_DECISION_COLLAPSE_REPORT.md (Phase 2.95 decisions)
- OWNER_REQUIRED_COMPRESSION_REPORT.md (compression decisions)
- FINAL_CLASSIFIED_REGISTER.md (all-phase summary)

---

## Collapse Classification Key

| Class | Meaning |
|---|---|
| CODE | Resolved from direct code inspection |
| DOC | Resolved from documentation cross-reference |
| WORKFLOW | Resolved from verified workflow analysis |
| ARCH | Resolved from architectural evidence |
| PATTERN | Resolved from established repository patterns |
| SINGLE-RATIONAL | Only one rational interpretation; no alternatives |

---

## DC-001: FSC-001 Frontend Consumer

| Field | Value |
|---|---|
| **ID** | DC-001 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-001 Frontend Consumer = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | Phase 3 FRONTEND_SCREEN_CATALOG.md SCR-001 (Login). FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-001 step 2. FRONTEND_AUTHORITY_MASTER.md token flow. |
| **Collapse class** | DOC |
| **Resolution** | `/login` screen (SCR-001). Tenant discovery → login → store user_id/tenant_id → fetch RBAC assignments → role dashboard redirect. |

---

## DC-002: FSC-002 Frontend Consumer

| Field | Value |
|---|---|
| **ID** | DC-002 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-002 Frontend Consumer = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | FRONTEND_SCREEN_CATALOG.md (Course Detail, Course Player). FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-003 Path A. |
| **Collapse class** | DOC |
| **Resolution** | `/learner/courses/:id` enroll button → POST /api/v1/enrollments → redirect to course player SCR-018. |

---

## DC-003: FSC-003 Frontend Consumer + API

| Field | Value |
|---|---|
| **ID** | DC-003 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-003 Frontend Consumer = "TBD – REQUIRES VERIFICATION"; API = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | Phase 2 addendum verified all 6 checkout API endpoints. FRONTEND_SCREEN_CATALOG.md SCR-019. FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-005. |
| **Collapse class** | DOC + CODE (Phase 2 addendum) |
| **Resolution** | Frontend: `/learner/checkout` (SCR-019). API: all 6 endpoints verified in Phase 2 addendum. |

---

## DC-004: FSC-004 Frontend Consumer + API

| Field | Value |
|---|---|
| **ID** | DC-004 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-004 Frontend Consumer = "TBD"; API = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | Phase 2 addendum verified progress endpoints. FRONTEND_SCREEN_CATALOG.md SCR-018 (Course Player). |
| **Collapse class** | DOC + CODE |
| **Resolution** | Frontend: course player `/learner/courses/:id/learn/:lid` (SCR-018). API: 3 progress endpoints verified. |

---

## DC-005: FSC-005 Frontend Consumer

| Field | Value |
|---|---|
| **ID** | DC-005 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-005 Frontend Consumer = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | FRONTEND_SCREEN_CATALOG.md SCR-021 (Certificate screen). FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-004 step 7. |
| **Collapse class** | DOC |
| **Resolution** | `/learner/certificates/:id` (SCR-021). Certificate viewer with download action. |

---

## DC-006: FSC-006 Frontend Consumer

| Field | Value |
|---|---|
| **ID** | DC-006 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-006 Frontend Consumer = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | FRONTEND_SCREEN_CATALOG.md SCR-012 (Timetable), SCR-023 (Attendance). FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-002. |
| **Collapse class** | DOC + WORKFLOW |
| **Resolution** | Admin: `/admin/batches/:id/timetable`. Teacher: `/teacher/batches/:id/attendance`. |

---

## DC-007: FSC-007 Frontend Consumer + Startup

| Field | Value |
|---|---|
| **ID** | DC-007 |
| **Item** | FSC-007 Frontend Consumer = "TBD"; "Startup mechanism unconfirmed (D-002)" |
| **Evidence** | FRONTEND_COMPONENT_INVENTORY.md PermissionGuard family. D-002 AUTO-CLOSED in Phase 2.9 — ASGI shims added. |
| **Collapse class** | DOC + CODE |
| **Resolution** | Frontend: all gated UI via PermissionGuard components. D-002: resolved, ASGI shims active. |

---

## DC-008: FSC-008 Frontend Consumer

| Field | Value |
|---|---|
| **ID** | DC-008 |
| **Item** | FULLSTACK_STITCHING_CONTRACT.md FSC-008 Domain Entity = "TBD"; Frontend Consumer = "TBD"; Redis = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | FRONTEND_WORKFLOW_TO_SCREEN_MAP.md WF-010. docs/integrations/lti-consumer-spec.md (domain entities listed). U9 H-010 (Redis nonce TTL=600s confirmed). |
| **Collapse class** | DOC + ARCH |
| **Resolution** | Domain entities: LtiLaunchContext, LtiNonce, LtiGradePassback. Frontend: `/lti/launch` special route. Redis: confirmed for nonce store. |

---

## DC-009: FSC-009 Frontend Consumer + Domain Entity

| Field | Value |
|---|---|
| **ID** | DC-009 |
| **Item** | FSC-009 Domain Entity = "TBD – REQUIRES VERIFICATION"; Frontend Consumer = "TBD – REQUIRES VERIFICATION" |
| **Evidence** | notification-service-spec.md (domain entities). orchestration.py + action_routing.py (confirmed). FRONTEND_SCREEN_CATALOG.md SCR-025. |
| **Collapse class** | DOC + CODE |
| **Resolution** | Domain entities: Notification, NotificationTemplate, WorkflowAction. Frontend: `/notifications` (SCR-025). |

---

## DC-010: FEATURE_SCOPE.md §1.10 Adaptive Learning TBD

| Field | Value |
|---|---|
| **ID** | DC-010 |
| **Item** | FEATURE_SCOPE.md: `| Adaptive learning | TBD – REQUIRES VERIFICATION |` |
| **Evidence** | PDC-006 (Phase 2.95): design doc exists (docs/designs/adaptive-learning-engine.md); no service in manifest; classified IMPLEMENTATION_GAP = FGAP-002. |
| **Collapse class** | DOC |
| **Resolution** | FGAP-002: design-only, deferred to adaptive learning sprint. Not permanent exclusion. |

---

## DC-011: FEATURE_SCOPE.md §2 Three TBDs

| Field | Value |
|---|---|
| **ID** | DC-011 |
| **Item** | FEATURE_SCOPE.md §2: adaptive engine "TBD", AI copilot "TBD", learner risk insights "TBD" |
| **Evidence** | PDC-006 (FGAP-002), PDC-007 (FGAP-003), PDC-008 (FGAP-004) all classified in Phase 2.95 |
| **Collapse class** | DOC |
| **Resolution** | All 3 updated to FGAP status with sprint classification. |

---

## DC-012: PRODUCT_WORKFLOWS.md WF-001 Onboarding Events TBD

| Field | Value |
|---|---|
| **ID** | DC-012 |
| **Item** | "Events emitted: TBD – REQUIRES VERIFICATION (onboarding events not confirmed in event_topics.json)" |
| **Evidence** | Direct inspection of infrastructure/event-bus/event_topics.json — 39 topics, zero tenant/onboarding events |
| **Collapse class** | CODE |
| **Resolution** | CONFIRMED: WF-001 is synchronous service chain only. No Kafka events emitted on tenant onboarding. |

---

## DC-013: PRODUCT_WORKFLOWS.md WF-005 JazzCash Webhook TBD

| Field | Value |
|---|---|
| **ID** | DC-013 |
| **Item** | "JazzCash webhook flow: TBD – REQUIRES VERIFICATION" |
| **Evidence** | integrations/payments/reconciliation.py: PaymentReconciliationEngine confirmed with run_reconciliation_pass(). integrations/payments/test_reconciliation.py: passing tests. |
| **Collapse class** | CODE |
| **Resolution** | PaymentReconciliationEngine handles webhook-triggered reconciliation. Order: PAID → RECONCILED. |

---

## DC-014: TBD-012 spec_index.json Consumer

| Field | Value |
|---|---|
| **ID** | DC-014 |
| **Item** | TBD_RESOLUTION_REGISTER.md TBD-012: spec_index.json consumer awaiting scripts audit |
| **Evidence** | Glob search of scripts/: no directory exists. spec_index.json uses old naming (underscores). No active consumer found anywhere in repository. |
| **Collapse class** | CODE + ARCH |
| **Resolution** | Stale artifact. No consumer. No action. Closed. |

---

## DC-015: OC-001 Checkout Persistence Timeline

| Field | Value |
|---|---|
| **ID** | DC-015 |
| **Item** | OWNER_CONFIRMATION_REGISTER.md OC-001: "When should checkout-service receive SQLite persistence?" awaiting owner confirmation |
| **Evidence** | Silence = acceptance per OWNER_CONFIRMATION_REGISTER.md usage rule. Phase 3 Frontend Authority Capture executed on recommended path. |
| **Collapse class** | PATTERN (governance rule) |
| **Resolution** | PROCEEDED: InMemoryCheckoutStore for development; SQLiteCheckoutStore in persistence sprint. |

---

## DC-016: OC-002 Cloud Target

| Field | Value |
|---|---|
| **ID** | DC-016 |
| **Item** | OC-002: cloud provider awaiting owner confirmation |
| **Evidence** | Silence = acceptance. Docker Compose confirmed in infrastructure/deployment/docker-compose.yml. |
| **Collapse class** | PATTERN |
| **Resolution** | PROCEEDED: Docker Compose + GitHub Actions default. Cloud provider at owner discretion. |

---

## DC-017: OC-003 File Upload API

| Field | Value |
|---|---|
| **ID** | DC-017 |
| **Item** | OC-003: binary upload endpoint — content-service vs media-service vs new wrapper |
| **Evidence** | Silence = acceptance. FileUpload component in FRONTEND_COMPONENT_INVENTORY.md built to media-service pattern. |
| **Collapse class** | PATTERN |
| **Resolution** | PROCEEDED: content-service (metadata) + media-service (binary). Upload form rendered with stub binary endpoint. |

---

## DC-018: OC-004 AI Tutor Scope

| Field | Value |
|---|---|
| **ID** | DC-018 |
| **Item** | OC-004: confirmed services vs full copilot vision |
| **Evidence** | Silence = acceptance. Phase 3 built AiTutorPanel component (lesson-level only). FGAP-003 tracks copilot overlay. |
| **Collapse class** | PATTERN + DOC |
| **Resolution** | PROCEEDED: ai-tutor + recommendation + course-gen in initial sprint. Copilot overlay = FGAP-003. |

---

## DC-019: AI_OPERATING_CONTEXT.md CURRENT_PHASE

| Field | Value |
|---|---|
| **ID** | DC-019 |
| **Item** | CURRENT_PHASE = "Governance Entry (Phase 1 complete — implementation pending)" |
| **Evidence** | Phase progression: Phase 2.9 → 2.95 → Compression → Phase 3 → Phase 3.25 all complete |
| **Collapse class** | SINGLE-RATIONAL |
| **Resolution** | Updated to "Phase 3.25 — Autonomous Gap Elimination complete (2026-06-23)" |

---

## DC-020: AI_OPERATING_CONTEXT.md Service Count

| Field | Value |
|---|---|
| **ID** | DC-020 |
| **Item** | FROZEN_DECISIONS: "Service count | 72 total: 69 HTTP + 3 class-based" — stale post Phase 2.9 |
| **Evidence** | Phase 2.9 added ASGI shims to 3 class-based services and updated manifest. They are now standard HTTP services. |
| **Collapse class** | CODE + ARCH |
| **Resolution** | Updated to "69 in manifest; 3 class-based services now have ASGI shims and updated manifest entries" |

---

## DC-021: AI_OPERATING_CONTEXT.md Parent Role TBD

| Field | Value |
|---|---|
| **ID** | DC-021 |
| **Item** | "Parents — monitor student progress (TBD — REQUIRES VERIFICATION)" |
| **Evidence** | PDC-009 classified as FGAP-001 (IMPLEMENTATION_GAP) in Phase 2.95. No parent-service in manifest. |
| **Collapse class** | DOC |
| **Resolution** | Updated to "FGAP-001: confirmed gap — parent-service not in manifest; parent portal sprint required" |

---

## DC-022: AI_OPERATING_CONTEXT.md R-005/R-013 Owner Decision Language

| Field | Value |
|---|---|
| **ID** | DC-022 |
| **Item** | KNOWN_RISKS: R-005 = "owner decision on persistence"; R-013 = "owner decision on cloud target" |
| **Evidence** | OWNER_REQUIRED_COMPRESSION_REPORT.md: R-005 → SAFE-DEFAULT (ITEM-08); R-013 → SAFE-DEFAULT (Docker Compose + GitHub Actions default) |
| **Collapse class** | DOC |
| **Resolution** | Updated to SAFE-DEFAULT language for both. |

---

## DC-023: BACKEND_GAP_REGISTER.md Summary Table

| Field | Value |
|---|---|
| **ID** | DC-023 |
| **Item** | Summary table said "8 open" — stale from pre-compression era |
| **Evidence** | All 8 "open" items have COMPRESSION annotations (SAFE-DEFAULT or AUTO-CLOSED) in the register |
| **Collapse class** | SINGLE-RATIONAL |
| **Resolution** | Summary table replaced with compression-resolved classification. 0 OWNER-REQUIRED items. |

---

## DC-024: PRODUCT_WORKFLOWS.md R-005 Owner Decision Language

| Field | Value |
|---|---|
| **ID** | DC-024 |
| **Item** | WF-005 WARNING: "Fix: R-005 (requires owner decision on persistence backend)" |
| **Evidence** | OWNER_REQUIRED_COMPRESSION_REPORT.md: ITEM-01 SAFE-DEFAULT — SQLite BaseRepository pattern |
| **Collapse class** | DOC |
| **Resolution** | Updated to SAFE-DEFAULT language. |

---

## Collapse Summary

| Phase | Items Collapsed | Method |
|---|---|---|
| Phase 2.9 | 13 | Approval elimination |
| Phase 2.95 | 14 | Residual decision collapse |
| OWNER-REQUIRED Compression | 22 (9 AUTO-CLOSED + 10 SAFE-DEFAULT + 3 OWNER-REQUIRED) | Compression |
| Phase 3.25 (this register) | 24 | Autonomous gap elimination |
| **Cumulative total collapsed** | **73** | — |

**Remaining items that CANNOT be collapsed:**
- OR-001 JWT_PRIVATE_KEY (CREDENTIAL — 1 item)
- OR-002 capability-resolution.md (PROTECTED ANCHOR — 1 item)
- OR-003 doc-precedence.md (PROTECTED ANCHOR — 1 item)
- FGAPs (IMPLEMENTATION GAPS requiring engineering sprints — 6 items)
- BACKEND-TBD service API inspection (TECHNICAL DISCOVERY — 19 items)

**True OWNER-REQUIRED decisions remaining: 3 (all non-blocking)**
**True open ambiguities remaining: 0**
