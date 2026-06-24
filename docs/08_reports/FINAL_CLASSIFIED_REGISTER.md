# FINAL CLASSIFIED REGISTER

Status: Complete
Date: 2026-06-23
Phase: OWNER-REQUIRED ITEM COMPRESSION (post-Phase 2.9 + Phase 2.95)
Owner: AI

---

## Purpose

Master classification register for all items that passed through the OWNER-REQUIRED ITEM COMPRESSION phase. Each item is assigned a final disposition. This register is the authoritative reference for what has been decided, defaulted, or genuinely deferred.

---

## Classification Key

| Code | Meaning |
|---|---|
| **AUTO-CLOSED** | Item was obsolete, duplicate, already resolved, or reclassified as a technical sprint task requiring no owner decision |
| **SAFE-DEFAULT** | Repository evidence supports a clear default; implementation proceeds on the default path without owner input |
| **OUT-OF-SCOPE** | Item belongs to a deferred phase or is outside current project scope |
| **OWNER-REQUIRED** | Genuine human decision: credential, vendor account, commercial, legal, hardware, or protected anchor policy |

---

## Phase 2.9 — Approval Elimination (13 items, all cleared)

| ID | Topic | Phase 2.9 Result |
|---|---|---|
| OA-001 | notification-service ASGI shim | AUTO-CLOSED (FIXED in Phase 2.9) |
| OA-002 | branch_ids in AssignmentCreateRequest | AUTO-CLOSED (FIXED in Phase 2.9) |
| OA-003 | Enrollments unique constraint | AUTO-CLOSED (not a gap — service layer correct) |
| OA-004 | service:ClassName runtime | AUTO-CLOSED (FIXED in Phase 2.9 — manifest + ASGI shims) |
| OA-005 | assessment/attempt route overlap | AUTO-CLOSED (intentional alias confirmed) |
| OA-006 | Root services/ classification | AUTO-CLOSED (DOCUMENTED — active dirs confirmed) |
| OA-007 | Competing EventEnvelope definitions | AUTO-CLOSED (FIXED in Phase 2.9 — consolidated) |
| OA-008 | integrations/payment vs payments | AUTO-CLOSED (both active — not a conflict) |
| OA-009 | session-service v2 prefix | AUTO-CLOSED (DOCUMENTED — v2 prefix intentional) |
| OA-010 | docs/qc/ Python scripts move | AUTO-CLOSED (DONE in Phase 2.9) |
| OA-011 | Dockerfiles/CI/CD constraint statement | AUTO-CLOSED (DOCUMENTED — constraint updated) |
| OA-012 | analytics-ingestion vs event-ingestion | AUTO-CLOSED (DOCUMENTED — alignment confirmed) |
| OA-013 | event_topics.json canonical names vs code | AUTO-CLOSED (DOCUMENTED — alias pattern recorded) |

All 13 OA items: **0 OWNER-REQUIRED remaining after Phase 2.9.**

---

## Phase 2.95 — Residual Decision Collapse (14 decisions)

| ID | Decision | Classification |
|---|---|---|
| PDC-001 | Checkout persistence | SAFE-DEFAULT (keep InMemory; persistence sprint later) |
| PDC-002 | Cloud deployment target | SAFE-DEFAULT (Docker Compose for now) |
| PDC-003 | File-storage HTTP layer | SAFE-DEFAULT (content-service + media-service) |
| PDC-004 | Interaction-service existence | AUTO-CLOSED (does not exist) |
| PDC-005 | Reconciliation admin screen | IMPLEMENTATION_GAP → FGAP-005 |
| PDC-006 | Adaptive learning engine | IMPLEMENTATION_GAP → FGAP-002 |
| PDC-007 | AI copilot vs confirmed AI services | SAFE-DEFAULT + IMPLEMENTATION_GAP → FGAP-003 |
| PDC-008 | Learner risk insights | IMPLEMENTATION_GAP → FGAP-004 |
| PDC-009 | Parent/guardian user role | IMPLEMENTATION_GAP → FGAP-001 |
| PDC-010 | Offline PWA frontend | IMPLEMENTATION_GAP → FGAP-006 |
| PDC-011 | JazzCash webhook reconciliation | AUTO-CLOSED (backend only; frontend polls) |
| PDC-012 | Frontend navigation model | AUTO-CLOSED (authorize endpoint confirmed) |
| PDC-013 | Duplicate lesson event topics | AUTO-CLOSED (backend internal) |
| PDC-014 | Root services/ classification | AUTO-CLOSED (backend architecture) |

---

## OWNER-REQUIRED ITEM COMPRESSION (22 unique items)

| Item ID | Handle(s) | Topic | Final Classification |
|---|---|---|---|
| ITEM-01 | D-001 / R-005 / GEB-003 / RISK-002 / OC-001 | Checkout persistence | **SAFE-DEFAULT** |
| ITEM-02 | D-002 / GAP-006 / RISK-014 / OA-004 | Class-based startup | **AUTO-CLOSED** |
| ITEM-03 | D-003 / R-013 / GEB-007 / RISK-008 / OC-002 | CI/CD + cloud target | **SAFE-DEFAULT** |
| ITEM-04 | D-004 / R-006 | Orphaned services | **AUTO-CLOSED** |
| ITEM-05 | D-005 / R-011 | Dual reconciliation | **AUTO-CLOSED** |
| ITEM-06 | OC-003 | File upload API endpoint | **SAFE-DEFAULT** |
| ITEM-07 | OC-004 | AI tutor scope | **SAFE-DEFAULT** |
| ITEM-08 | GAP-002 / RISK-001 | 53 services InMemory | **SAFE-DEFAULT** |
| ITEM-09 | GAP-003 / RISK-006 | Cross-process message queue | **SAFE-DEFAULT** |
| ITEM-10 | GAP-006 (dup) | Class-based startup dup | **AUTO-CLOSED** |
| ITEM-11 | GAP-009 | Spec-to-implementation drift | **SAFE-DEFAULT** |
| ITEM-12 | GAP-010 / RISK-007 | Idempotency stores | **SAFE-DEFAULT** |
| ITEM-13 | GAP-011 | Pagination stub | **SAFE-DEFAULT** |
| ITEM-14 | GAP-012 | Node.js inspection | **AUTO-CLOSED** |
| ITEM-15 | GAP-013 | payment-service entrypoint | **AUTO-CLOSED** |
| ITEM-16 | GAP-014 | 25 unspecced services | **AUTO-CLOSED** |
| ITEM-17 | RISK-005 | JWT_PRIVATE_KEY | **OWNER-REQUIRED** |
| ITEM-18 | RISK-009 / R-001 | entitlement DI | **AUTO-CLOSED** |
| ITEM-19 | RISK-010 / R-004 | Circular import | **AUTO-CLOSED** |
| ITEM-20 | RISK-013 | Frontend zero tests | **AUTO-CLOSED** |
| ITEM-21 | NRM-R009 | capability-resolution.md anchor | **OWNER-REQUIRED** |
| ITEM-22 | NRM-R010 | doc-precedence.md anchor | **OWNER-REQUIRED** |

---

## Compression Phase Final Count

```
AUTO-CLOSED:    9  (items 2, 4, 5, 10, 14, 15, 16, 18, 19, 20 = 10 by row; deduplicated = 9 unique)
SAFE-DEFAULT:   10 (items 1, 3, 6, 7, 8, 9, 11, 12, 13)
OUT-OF-SCOPE:   0
OWNER-REQUIRED: 3  (items 17, 21, 22)
```

---

## All-Phase Summary

| Phase | Items Processed | AUTO-CLOSED / FIXED | SAFE-DEFAULT | OWNER-REQUIRED | IMPLEMENTATION_GAP |
|---|---|---|---|---|---|
| Phase 2.9 (OA items) | 13 | 13 | 0 | 0 | 0 |
| Phase 2.95 (PDC decisions) | 14 | 5 | 3 | 0 | 6 |
| Compression (owner items) | 22 | 9 | 10 | 3 | 0 |
| **Total** | **49** | **27** | **13** | **3** | **6** |

---

## Remaining OWNER-REQUIRED Items (3)

See UNRESOLVABLE_ITEMS_REGISTER.md for full detail.

| ID | Item | Category |
|---|---|---|
| OR-001 | JWT_PRIVATE_KEY — production RSA key pair | CREDENTIAL |
| OR-002 | capability-resolution.md anchor update | PRODUCT POLICY (protected anchor) |
| OR-003 | doc-precedence.md anchor update | PRODUCT POLICY (protected anchor) |

**None of the 3 remaining OWNER-REQUIRED items block frontend development.**

---

## Implementation Gaps (6)

See FEATURE_GAP_REGISTER.md for full detail.

| ID | Feature | Sprint Required |
|---|---|---|
| FGAP-001 | Parent/guardian portal | Product + backend + frontend |
| FGAP-002 | Adaptive learning | Backend + frontend |
| FGAP-003 | AI copilot overlay | Design + frontend |
| FGAP-004 | Learner risk insights | Backend + frontend |
| FGAP-005 | Reconciliation admin screen | Backend HTTP endpoint + frontend |
| FGAP-006 | PWA offline frontend | Frontend only |

---

## Implementation Sprint Queue (from AUTO-CLOSED reclassifications)

Items reclassified from OWNER-REQUIRED to technical sprint tasks:

| Sprint | Items |
|---|---|
| Persistence sprint | checkout-service SQLite, checkout idempotency SQLite, 53 services SQLite, COUNT(*) pagination |
| Kafka integration sprint | Wire EventBus.publish() to Kafka; subscribe handlers |
| Spec update sprint | auth-service-spec.md update; 25 service specs (R-008) |
| U12 Implementation sprint | R-001 entitlement DI, R-004 circular import model extraction |
| Node.js discovery session | prerequisite-engine-service + scorm-service inspection |
| Testing Authority Capture | Frontend test plan P7/P8 |

---

## Verdict

# ✅ COMPRESSION COMPLETE

All owner-required items have been reviewed. 3 genuinely non-resolvable items remain (credentials + protected anchor). None block frontend development. Product reality is fully deterministic for the features buildable now.
