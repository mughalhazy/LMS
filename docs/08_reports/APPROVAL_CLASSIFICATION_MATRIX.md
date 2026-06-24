# APPROVAL CLASSIFICATION MATRIX

Status: Complete
Date: 2026-06-23
Phase: Phase 2.9 — Approval Elimination
Owner: AI

---

## Purpose

Classifies every OA item by type of resolution, evidence strength, and action category. Used to demonstrate that the approval-elimination process was systematic and evidence-driven.

---

## Classification Scheme

| Class | Meaning |
|---|---|
| **DETERMINABLE-FIX** | Evidence fully establishes single correct outcome; code/manifest fix applied |
| **DETERMINABLE-DOC** | Evidence fully establishes correct state; documentation correction applied |
| **EVIDENCE-CLOSED** | Evidence shows the "gap" is not a gap — existing behavior is correct |
| **EVIDENCE-PATTERN** | Evidence reveals an intentional design pattern; closed without change |

---

## Matrix

| OA ID | Topic | Class | Evidence Source | Evidence Strength | Action |
|---|---|---|---|---|---|
| OA-001 | notification-service ASGI shim | DETERMINABLE-FIX | `backend/services/notification-service/app/main.py` full read | HIGH — no ambiguity, exact pattern match to Task 7 | Added FastAPI `app` object + 8 route handlers |
| OA-002 | branch_ids schema gap | DETERMINABLE-FIX | schemas.py, models.py, service.py, store_db.py | HIGH — model has field, service reads it, API schema was missing it | Added field to request schema + service constructor |
| OA-003 | Enrollment unique constraint | EVIDENCE-CLOSED | store_db.py, store.py (CAT-016 comment), service.py (active_for_learner_course) | HIGH — service enforces logical constraint; INDEX allows re-enrollment by design | No code change; docs updated |
| OA-004 | service:ClassName manifest | DETERMINABLE-FIX | All 3 backend service main.py files (full read), service-manifest.json | HIGH — no loader found; backend implementations complete | ASGI shims + manifest path updates |
| OA-005 | assessment/attempt overlap | EVIDENCE-PATTERN | assessment-service/app/main.py lines 117–142 (AUD-005/006/007 comments) | HIGH — spec section references in code comments prove design intent | No change; closed |
| OA-006 | Root services/ classification | DETERMINABLE-DOC | Import grep: payment-service, tenant-service | MEDIUM — guarded imports confirm active; absence of import = legacy (absence of evidence = evidence of absence for this case) | Documentation classification update |
| OA-007 | Competing EventEnvelope | DETERMINABLE-FIX | course-service schemas.py, service.py (line 354), consumers.py | HIGH — consumers already use shared; service used local only for internal store | Removed local class; updated service import |
| OA-008 | integrations/payment vs payments | EVIDENCE-CLOSED | Import grep across codebase | HIGH — both have confirmed consumers in different layers | No change; documented as dual-active |
| OA-009 | session-service v2 prefix | DETERMINABLE-DOC | session-service/app/main.py, api-versioning-strategy.md | HIGH — v2 in code is intentional versioning; doc simply lacked the exception note | Added exception section to versioning doc |
| OA-010 | docs/qc/ scripts move | DETERMINABLE-FIX | scripts/fix_repo_anchor_paths.py grep, full codebase import grep | HIGH — zero external dependencies on docs/qc/ path | Files moved to validation/ |
| OA-011 | Dockerfiles constraint | DETERMINABLE-DOC | infrastructure/ glob, AI_OPERATING_CONTEXT.md read | HIGH — files confirmed present; constraint text was factually wrong | Updated constraint in 3 authority docs |
| OA-012 | analytics-ingestion name | DETERMINABLE-DOC | service-manifest.json, event_topics.json (all entries) | HIGH — both authoritative sources use `event-ingestion-service` | Corrected 2 documentation files |
| OA-013 | Event topic canonical names | DETERMINABLE-DOC | enrollment-service consumers.py grep, event_topics.json | MEDIUM — dual-subscribe is an observed pattern; future standardization = sprint work | Documented pattern + policy statement |

---

## Evidence Strength Distribution

| Strength | Count | Items |
|---|---|---|
| HIGH | 11 | OA-001, 002, 003, 004, 005, 007, 008, 009, 010, 011, 012 |
| MEDIUM | 2 | OA-006, OA-013 |
| LOW | 0 | — |

---

## Resolution Action Distribution

| Action | Count | Items |
|---|---|---|
| Code fix applied | 5 | OA-001, OA-002, OA-004, OA-007, OA-010 |
| Documentation updated | 5 | OA-009, OA-011, OA-012, OA-013, OA-006 |
| Closed as non-gap | 3 | OA-003, OA-005, OA-008 |
| Escalated to owner | 0 | — |

---

## Items That Could Have Been Escalated But Were Not

The following items were initially framed as needing owner input but were resolved from evidence:

- **OA-003** (enrollment unique constraint): Could have been "owner decides whether to add DB constraint." Evidence shows the service-layer pattern is correct by design — the comment CAT-016 documents logical intent, and `active_for_learner_course()` enforces it. DB UNIQUE would break re-enrollment. No decision needed.

- **OA-004** (service:ClassName): Could have been "owner decides which loader to use." Evidence shows no loader exists anywhere; backend/services/ implementations are functionally complete HTTP services. Single valid outcome.

- **OA-005** (assessment/attempt overlap): Could have been "owner decides ownership split." Evidence in code comments (AUD-005/006/007 with spec section references) proves the intent. No decision needed.

- **OA-008** (payment/payments): Could have been "owner decides which to keep." Evidence shows both are active consumers. Neither can be removed. No decision needed.
