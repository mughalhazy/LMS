# OWNER-REQUIRED ITEM COMPRESSION REPORT

Status: Complete
Date: 2026-06-23
Phase: OWNER-REQUIRED ITEM COMPRESSION (pre-Frontend Authority Capture)
Owner: AI

---

## Purpose

Review every OWNER-REQUIRED item remaining after autonomous gap elimination (Phase 2.9) and decision collapse (Phase 2.95). Apply the mandatory compression test: OWNER-REQUIRED survives only for credentials, vendor account setup, payment/tax/legal/compliance, hardware procurement, regulatory/tax, or product policy decisions that cannot be inferred from repository evidence.

---

## Source Inventory

Items reviewed from the following documents:

| Source | Items |
|---|---|
| AI_OPERATING_CONTEXT.md OPEN_ARCHITECTURAL_QUESTIONS | D-001, D-002, D-003, D-004, D-005 |
| OWNER_CONFIRMATION_REGISTER.md | OC-001, OC-002, OC-003, OC-004 |
| BACKEND_GAP_REGISTER.md — "Owner Action" fields | GAP-002, GAP-003, GAP-006, GAP-009, GAP-010, GAP-011, GAP-012, GAP-013, GAP-014 |
| BACKEND_RISK_REGISTER.md — "Required Action" fields | RISK-001, RISK-002, RISK-005, RISK-006, RISK-007, RISK-008, RISK-009, RISK-010, RISK-013 |
| U11_LMS_FINAL_RECOMMENDATION.md REQUIRES_OWNER_DECISION | R-005, R-006, R-009, R-011, R-013 |
| NORMALIZATION_REMEDIATION_REPORT.md DEFERRED items | NRM-R009, NRM-R010 |

**Total handles reviewed: 41**
**Unique items (after deduplication): 22**

---

## Compression Analysis — Item by Item

---

### ITEM-01: Checkout Persistence Backend

| Field | Value |
|---|---|
| **Handles** | D-001 / R-005 / GEB-003 / RISK-002 / OC-001 |
| **Current label** | OWNER-REQUIRED → OWNER_CONFIRMATION_ONLY |
| **Original question** | Does backend/checkout-service handle DB persistence for orders/sessions? |
| **Evidence reviewed** | 16 services wired to SQLiteXStore via BaseRepository (Task 7). checkout-service still uses InMemoryCheckoutStore per BACKEND_GAP_REGISTER GAP-002. Pattern for SQLite persistence is fully established in shared/db/engine.py. |
| **Frontend UX impact** | No — checkout flow screens are identical regardless of persistence layer |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Persistence sprint required (backend only); zero frontend coupling |
| **Genuinely owner-required?** | NO — not credentials, vendor, legal, hardware, or regulatory. SQLite is the confirmed default pattern. |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Keep InMemoryCheckoutStore for development. Add checkout-service store_db.py (SQLiteCheckoutStore) in dedicated persistence sprint using BaseRepository from shared/db/engine.py — same pattern as 16 already-wired services. |
| **Action taken** | Closed in AI_OPERATING_CONTEXT D-001. Annotated in BACKEND_GAP_REGISTER GAP-002. Recorded in UNRESOLVABLE_ITEMS_REGISTER: n/a. |

---

### ITEM-02: Class-Based Service Startup

| Field | Value |
|---|---|
| **Handles** | D-002 / GAP-006 / RISK-014 / OA-004 |
| **Current label** | OWNER-REQUIRED |
| **Original question** | What runtime interprets `service:ClassName` in service-manifest.json? |
| **Evidence reviewed** | Phase 2.9: No loader found anywhere in repository. Manifest updated — capability-registry, config-service, entitlement-service now registered to backend/services/ equivalents. ASGI shims added. D-002 already marked RESOLVED in AI_OPERATING_CONTEXT. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Already resolved. |
| **Genuinely owner-required?** | NO — and already resolved |
| **Final classification** | **AUTO-CLOSED** |
| **Default** | RESOLVED. Manifest entries corrected. ASGI shims in place. |
| **Action taken** | Closed. Existing RESOLVED note in AI_OPERATING_CONTEXT D-002 is correct. |

---

### ITEM-03: CI/CD Platform + Cloud Deployment Target

| Field | Value |
|---|---|
| **Handles** | D-003 / R-013 / GEB-007 / RISK-008 / OC-002 |
| **Current label** | OWNER-REQUIRED |
| **Original question** | Which CI/CD platform? Docker? Cloud deployment target? |
| **Evidence reviewed** | OA-011 (Phase 2.9): Dockerfiles and CI/CD files confirmed present — Dockerfile.python, Dockerfile.node in infrastructure/deployment/docker/; docker-compose.yml (deployment + observability); deploy-backend.yml in infrastructure/deployment/cicd/. Constraint was updated to "do not add new files." Docker Compose is the confirmed local/staging runtime. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Infrastructure sprint required for production, but does not block any current engineering |
| **Genuinely owner-required?** | PARTIALLY — Docker Compose and GitHub Actions are safe defaults from evidence. Production cloud provider (AWS / GCP / Azure / DigitalOcean) is a genuine vendor/commercial decision but does not block current engineering. |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Docker Compose for local development and staging (confirmed in infrastructure/). GitHub Actions for CI (safe industry default; no pipeline written, but no competing CI config exists). Production cloud provider: deferred — owner confirms when approaching production launch. Non-blocking. |
| **Action taken** | Closed as blocking item. Updated AI_OPERATING_CONTEXT D-003. Cloud provider noted as non-blocking deferred choice only. |

---

### ITEM-04: Orphaned Services (file-storage + interaction-service)

| Field | Value |
|---|---|
| **Handles** | D-004 / R-006 |
| **Current label** | OWNER-REQUIRED |
| **Original question** | Keep or delete services/file-storage/ and services/interaction-service/? |
| **Evidence reviewed** | PDC-003 (Phase 2.95): file-storage/ is an active domain library referenced in MO-023 Phase B intent. PDC-004 (Phase 2.95): interaction-service has no code, no design, no product intent — does not exist as a real service. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | No action needed |
| **Genuinely owner-required?** | NO — evidence is conclusive for both |
| **Final classification** | **AUTO-CLOSED** (both parts) |
| **Default** | file-storage/: retain as domain library (MO-023 Phase B intent confirmed). interaction-service/: does not exist; no action. |
| **Action taken** | Closed. PDC-003/PDC-004 evidence sufficient. |

---

### ITEM-05: Dual Reconciliation (reconciliation.py)

| Field | Value |
|---|---|
| **Handles** | D-005 / R-011 |
| **Current label** | OWNER-REQUIRED |
| **Original question** | Is services/commerce/reconciliation.py actively used? Does it duplicate integrations/payments/reconciliation.py? |
| **Evidence reviewed** | PDC-005 (Phase 2.95): both files confirmed active. services/commerce/reconciliation.py is domain business logic (reconciliation algorithm). integrations/payments/reconciliation.py is the JazzCash/EasyPaisa adapter-level reconciliation. Different layers, different responsibilities. FGAP-005 tracks the missing HTTP endpoint + admin screen sprint. |
| **Frontend UX impact** | No (backend only until FGAP-005 sprint) |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | FGAP-005 — HTTP endpoint + admin screen sprint; tracked separately |
| **Genuinely owner-required?** | NO — evidence establishes both are active with different roles |
| **Final classification** | **AUTO-CLOSED** |
| **Default** | Both files confirmed active. FGAP-005 tracks sprint for HTTP endpoint + admin screen. |
| **Action taken** | Closed. Updated AI_OPERATING_CONTEXT D-005. |

---

### ITEM-06: File Upload API Endpoint

| Field | Value |
|---|---|
| **Handles** | OC-003 |
| **Current label** | OWNER_CONFIRMATION_ONLY |
| **Original question** | Which HTTP service exposes the file/binary upload endpoint — content-service, media-service, or new file-storage HTTP wrapper? |
| **Evidence reviewed** | service-manifest.json: both content-service (8096) and media-service (8119) are registered. AI_OPERATING_CONTEXT: content-service owns content metadata; binary upload responsibility not explicitly assigned. Pattern: content-service handles content registration metadata; media-service handles binary media assets. |
| **Frontend UX impact** | Binary upload form has a stub action until content sprint confirms endpoint — not a blocker |
| **Navigation impact** | No |
| **Workflow impact** | Minor — content upload workflow has a TBD binary upload step |
| **Permission impact** | No |
| **Implementation impact** | Content sprint: confirm which service handles multipart upload |
| **Genuinely owner-required?** | NO — the safe default is architecturally derivable: content-service for metadata; media-service for binary |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | content-service: content metadata registration. media-service: binary file/video/SCORM/image upload. Frontend stub upload form renders; actual endpoint wired in content sprint. If owner confirms file-storage HTTP wrapper instead, ASGI shim pattern applies. |
| **Action taken** | Closed. OC-003 removed from blocking status. |

---

### ITEM-07: AI Tutor Scope Boundary

| Field | Value |
|---|---|
| **Handles** | OC-004 |
| **Current label** | OWNER_CONFIRMATION_ONLY |
| **Original question** | Is the frontend AI feature limited to ai-tutor-service, or does it include the full "AI learning copilot" design? |
| **Evidence reviewed** | PDC-007 (Phase 2.95): ai-tutor-service (8138), recommendation-service (8101), course-generation-service (8117) all confirmed in manifest. AI copilot overlay design doc exists (docs/designs/) — confirmed as gap, not current scope. FGAP-003 tracks copilot sprint. |
| **Frontend UX impact** | No — three confirmed AI UI components build now; copilot overlay is additive |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | FGAP-003 — copilot overlay sprint tracked separately |
| **Genuinely owner-required?** | NO — confirmed services are buildable; copilot is gap |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Build now: ai-tutor chat panel per lesson (ai-tutor-service), recommendations widget (recommendation-service), course generation for admins (course-generation-service). Copilot overlay: FGAP-003 — deferred to AI copilot sprint. |
| **Action taken** | Closed. OC-004 removed from blocking status. |

---

### ITEM-08: 53 Services Still InMemory

| Field | Value |
|---|---|
| **Handles** | GAP-002 / RISK-001 |
| **Current label** | OWNER-REQUIRED ("Architecture decision on production persistence backend") |
| **Evidence reviewed** | 16 services use SQLite via BaseRepository (shared/db/engine.py). Pattern is fully established, documented, and tested. SQLite survives restart; is single-file; is production-viable for low-to-medium scale. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Persistence sprint: write store_db.py for each of the 53 remaining services |
| **Genuinely owner-required?** | NO — the persistence pattern is established; SQLite is the confirmed default; no new vendor/architecture decision required |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | SQLite for all 53 remaining services using BaseRepository pattern from shared/db/engine.py. When owner decides to scale to PostgreSQL, migration is a separate sprint. |
| **Action taken** | Annotated in BACKEND_GAP_REGISTER GAP-002. |

---

### ITEM-09: Cross-Process Message Queue Platform

| Field | Value |
|---|---|
| **Handles** | GAP-003 / RISK-006 |
| **Current label** | OWNER-REQUIRED ("Decision on cross-process message queue platform") |
| **Evidence reviewed** | infrastructure/event-bus/event_bus_config.json: `"platform": "kafka"`, cluster `lms-domain-events`, bootstrap servers kafka-0/1/2.lms.svc.cluster.local:9092. infrastructure/event-bus/validate_event_bus.py: same Kafka config. The platform decision has already been made and committed to infrastructure config. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Kafka broker sprint: wire EventBus.publish() to Kafka producer; subscribe handlers to Kafka consumer groups |
| **Genuinely owner-required?** | NO — Kafka is confirmed in repository infrastructure config |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Kafka per infrastructure/event-bus/event_bus_config.json. No re-decision needed. In-process EventBus (already functional) serves as dev fallback. |
| **Action taken** | Annotated in BACKEND_GAP_REGISTER GAP-003. |

---

### ITEM-10: Class-Based Startup (GAP-006 reference)

| Field | Value |
|---|---|
| **Handles** | GAP-006 (duplicate of ITEM-02) |
| **Final classification** | **AUTO-CLOSED** (duplicate — see ITEM-02) |

---

### ITEM-11: Spec-to-Implementation Drift (auth-service)

| Field | Value |
|---|---|
| **Handles** | GAP-009 |
| **Current label** | OWNER-REQUIRED ("Align spec to implementation or implement DB persistence") |
| **Evidence reviewed** | auth-service-spec.md defines refresh_token_family, login_audit_event, key_metadata entities. Task 7: auth-service now uses SQLiteAuthStore with 7 tables (auth_tenants, auth_user_credentials, auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events). auth_refresh_tokens has lineage columns. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Spec update sprint (doc-only): update auth-service-spec.md to reflect SQLite implementation |
| **Genuinely owner-required?** | NO — updating a spec to match confirmed implementation is an autonomous doc task |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Update auth-service-spec.md to reflect SQLite implementation (7 tables). refresh_token_family → auth_refresh_tokens with lineage columns. login_audit_event → auth_audit_log. key_metadata → documented in auth-rsa-key-design.md. |
| **Action taken** | Annotated in BACKEND_GAP_REGISTER GAP-009. |

---

### ITEM-12: Idempotency Stores Reset on Restart

| Field | Value |
|---|---|
| **Handles** | GAP-010 / RISK-007 |
| **Current label** | OWNER-REQUIRED ("Persistent idempotency store required for production") |
| **Evidence reviewed** | progress-service already uses SQLiteIdempotencyStore (Task 7 partial). checkout-service still uses InMemoryIdempotencyStore. SQLite idempotency store pattern is established in progress-service. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Persistence sprint: add SQLiteIdempotencyStore to checkout-service (same pattern) |
| **Genuinely owner-required?** | NO — technical sprint task; pattern is established |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Add SQLiteIdempotencyStore to checkout-service in persistence sprint. Same pattern as progress-service. |
| **Action taken** | Annotated in BACKEND_GAP_REGISTER GAP-010. |

---

### ITEM-13: Pagination Total Stub

| Field | Value |
|---|---|
| **Handles** | GAP-011 |
| **Current label** | OWNER-REQUIRED ("Implement true count query when DB is added") |
| **Evidence reviewed** | enrollment-service returns `"total": len(items)` not a true DB count. Code comment: `# stub total; real impl would query count separately`. SQLite COUNT(*) query is standard. |
| **Frontend UX impact** | Pagination accuracy for large datasets — but this is a backend implementation detail |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Persistence sprint: add COUNT(*) query to enrollment-service list handler |
| **Genuinely owner-required?** | NO — standard SQL implementation task |
| **Final classification** | **SAFE-DEFAULT** |
| **Default** | Implement `SELECT COUNT(*) FROM enrollments WHERE tenant_id=?` in enrollment-service list handler during persistence sprint. |
| **Action taken** | Annotated in BACKEND_GAP_REGISTER GAP-011. |

---

### ITEM-14: Node.js Services Not Inspected

| Field | Value |
|---|---|
| **Handles** | GAP-012 |
| **Current label** | OWNER-REQUIRED ("Node.js service inspection required in a separate session") |
| **Evidence reviewed** | prerequisite-engine-service (8124) and scorm-service (8131) are Node.js. Internal implementation has not been inspected. This is a technical discovery task, not a business decision. |
| **Frontend UX impact** | No (until Node.js service outputs are consumed) |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Technical sprint: AI inspects both Node.js services; outputs their API surface |
| **Genuinely owner-required?** | NO — code inspection is an AI-executable task |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | TECHNICAL SPRINT ITEM: Node.js service discovery session |
| **Action taken** | Removed from owner queue. Annotated in BACKEND_GAP_REGISTER GAP-012. |

---

### ITEM-15: payment-service Non-Standard Entrypoint

| Field | Value |
|---|---|
| **Handles** | GAP-013 |
| **Current label** | OWNER-REQUIRED ("Verify payment-service entrypoint and document") |
| **Evidence reviewed** | payment-service uses `api:app` in manifest (not `app.main:app`). This means FastAPI app is in api.py at service root. Technical verification via Read tool is sufficient. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Verification only: confirm api.py exists and has FastAPI app; update manifest comment if needed |
| **Genuinely owner-required?** | NO — technical verification, AI-executable |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | TECHNICAL VERIFICATION TASK: verify payment-service api.py entrypoint |
| **Action taken** | Removed from owner queue. Annotated in BACKEND_GAP_REGISTER GAP-013. |

---

### ITEM-16: 25 Services Without Engineering Specs

| Field | Value |
|---|---|
| **Handles** | GAP-014 |
| **Current label** | OWNER-REQUIRED ("Authorize spec writing for unspecced services") |
| **Evidence reviewed** | REVISED_DECISION_ESCALATION_MATRIX: spec writing for services is within AI autonomous scope. R-008 in U11_LMS_FINAL_RECOMMENDATION.md: "DOC_ONLY" — ready to implement, no decision needed. Spec writing does not require owner authorization under established governance. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Documentation sprint: write 25 service specs |
| **Genuinely owner-required?** | NO — autonomous documentation task |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | AUTONOMOUS DOC SPRINT: write 25 service specs |
| **Action taken** | Removed from owner queue. Annotated in BACKEND_GAP_REGISTER GAP-014. |

---

### ITEM-17: JWT_PRIVATE_KEY — Ephemeral RSA Key

| Field | Value |
|---|---|
| **Handles** | RISK-005 |
| **Current label** | OWNER-REQUIRED (implicit — "Set JWT_PRIVATE_KEY to stable PEM-encoded RSA private key") |
| **Evidence reviewed** | auth-service generates ephemeral in-process RSA key when JWT_PRIVATE_KEY env var is not set. Every restart invalidates all tokens. Production deployment requires a stable key. This key must be generated outside the codebase and stored securely (env var, secrets manager). |
| **Frontend UX impact** | No (infra-level) |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Deployment credential: must be set before production |
| **Genuinely owner-required?** | **YES** — CREDENTIAL. RSA private key must be generated and owned by the operator. Cannot be inferred or defaulted from repository. |
| **Final classification** | **OWNER-REQUIRED** |
| **Required action** | Owner generates RSA-2048 or RSA-4096 key pair. Private key set as JWT_PRIVATE_KEY env var in auth-service. Public key distributed as JWT_PUBLIC_KEY env var to all 32 consuming services. Use secrets manager (not .env) for production. |

---

### ITEM-18: entitlement-service DI (R-001)

| Field | Value |
|---|---|
| **Handles** | RISK-009 / R-001 |
| **Current label** | OWNER-REQUIRED (implied by RISK-009 "Required Action") |
| **Evidence reviewed** | U11_LMS_FINAL_RECOMMENDATION.md: R-001 classified as ARCHITECTURE_FIX, READY TO IMPLEMENT. No owner decision needed. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Implementation sprint (U12 R-001): inject EventBus via constructor instead of hard import |
| **Genuinely owner-required?** | NO — engineering task; classified READY TO IMPLEMENT |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | IMPLEMENTATION SPRINT TASK (U12 Phase 2): R-001 DI refactor |
| **Action taken** | Removed from owner queue. |

---

### ITEM-19: Circular Import (R-004)

| Field | Value |
|---|---|
| **Handles** | RISK-010 / R-004 |
| **Current label** | OWNER-REQUIRED (implied by RISK-010 "Required Action") |
| **Evidence reviewed** | U11_LMS_FINAL_RECOMMENDATION.md: R-004 classified as ARCHITECTURE_FIX, READY TO IMPLEMENT. No owner decision needed. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Implementation sprint (U12 Phase 2): extract shared models to break commerce ↔ subscription cycle |
| **Genuinely owner-required?** | NO — engineering task; classified READY TO IMPLEMENT |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | IMPLEMENTATION SPRINT TASK (U12 Phase 2): R-004 model extraction |
| **Action taken** | Removed from owner queue. |

---

### ITEM-20: Frontend Zero Tests

| Field | Value |
|---|---|
| **Handles** | RISK-013 |
| **Current label** | OWNER-REQUIRED (implied by RISK-013 "Required Action") |
| **Evidence reviewed** | Frontend test plan P7/P8 referenced in AI_OPERATING_CONTEXT KNOWN_RISKS. Testing Authority Capture is a distinct project phase. This is a technical sprint, not an owner decision. |
| **Frontend UX impact** | N/A (test infrastructure, not UX) |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Testing Authority Capture sprint |
| **Genuinely owner-required?** | NO — technical sprint; no business or credential decision |
| **Final classification** | **AUTO-CLOSED** |
| **Reclassified as** | TESTING AUTHORITY CAPTURE item (T-001) |
| **Action taken** | Removed from owner queue. |

---

### ITEM-21: capability-resolution.md Anchor Update

| Field | Value |
|---|---|
| **Handles** | NRM-R009 |
| **Current label** | DEFERRED — owner required (protected anchor) |
| **Evidence reviewed** | NORMALIZATION_REMEDIATION_REPORT.md R-009: Update capability-resolution.md to reflect confirmed 4-level config hierarchy (global→country→segment→tenant). REVISED_DECISION_ESCALATION_MATRIX: updating docs/anchors/*.md requires approval. The doc content update reflects established policy (already locked in AI_OPERATING_CONTEXT), but the document itself is classified as a protected anchor — modifying it requires governance approval. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Owner approval needed to update anchor doc |
| **Genuinely owner-required?** | **YES** — PRODUCT POLICY. Protected anchor document. Escalation matrix explicitly requires owner approval for anchor modifications. The content change is known (4-level hierarchy confirmed), but the governance rule requires human sign-off. |
| **Final classification** | **OWNER-REQUIRED** |
| **Required action** | Owner reviews the confirmed 4-level config resolution (global→country→segment→tenant) and approves update to capability-resolution.md. Content is already established in AI_OPERATING_CONTEXT; approval is the only missing element. |

---

### ITEM-22: doc-precedence.md Anchor Update

| Field | Value |
|---|---|
| **Handles** | NRM-R010 |
| **Current label** | DEFERRED — owner required (protected anchor) |
| **Evidence reviewed** | NORMALIZATION_REMEDIATION_REPORT.md R-010: Update doc-precedence.md to reflect TIER 0–5 authority model. Protected anchor. Same governance rule applies as NRM-R009. |
| **Frontend UX impact** | No |
| **Navigation impact** | No |
| **Workflow impact** | No |
| **Permission impact** | No |
| **Implementation impact** | Owner approval needed to update anchor doc |
| **Genuinely owner-required?** | **YES** — PRODUCT POLICY. Protected anchor document. |
| **Final classification** | **OWNER-REQUIRED** |
| **Required action** | Owner reviews TIER 0–5 authority model (established in NORMALIZATION_REMEDIATION_REPORT.md, confirmed in DOCUMENT_CLASSIFICATION_MATRIX.md) and approves update to doc-precedence.md. |

---

## Final Count

```
AUTO-CLOSED:    9
SAFE-DEFAULT:   10
OUT-OF-SCOPE:   0
OWNER-REQUIRED: 3
```

---

## Summary Table

| Item | Handles | Final Classification | Category |
|---|---|---|---|
| ITEM-01 | D-001/R-005/GEB-003/RISK-002/OC-001 | SAFE-DEFAULT | Checkout persistence → SQLite sprint |
| ITEM-02 | D-002/GAP-006/RISK-014/OA-004 | AUTO-CLOSED | Class-based startup resolved Phase 2.9 |
| ITEM-03 | D-003/R-013/GEB-007/RISK-008/OC-002 | SAFE-DEFAULT | Docker Compose confirmed; cloud deferred |
| ITEM-04 | D-004/R-006 | AUTO-CLOSED | interaction-service: doesn't exist; file-storage: keep |
| ITEM-05 | D-005/R-011 | AUTO-CLOSED | Reconciliation resolved Phase 2.95 (FGAP-005) |
| ITEM-06 | OC-003 | SAFE-DEFAULT | content-service + media-service for upload |
| ITEM-07 | OC-004 | SAFE-DEFAULT | AI tutor confirmed; copilot = FGAP-003 |
| ITEM-08 | GAP-002/RISK-001 | SAFE-DEFAULT | SQLite for 53 remaining services |
| ITEM-09 | GAP-003/RISK-006 | SAFE-DEFAULT | Kafka per event_bus_config.json |
| ITEM-10 | GAP-006 (dup) | AUTO-CLOSED | Duplicate of ITEM-02 |
| ITEM-11 | GAP-009 | SAFE-DEFAULT | Update spec to match SQLite implementation |
| ITEM-12 | GAP-010/RISK-007 | SAFE-DEFAULT | SQLiteIdempotencyStore in persistence sprint |
| ITEM-13 | GAP-011 | SAFE-DEFAULT | COUNT(*) query in persistence sprint |
| ITEM-14 | GAP-012 | AUTO-CLOSED | Technical sprint: Node.js inspection |
| ITEM-15 | GAP-013 | AUTO-CLOSED | Technical verification: payment-service api.py |
| ITEM-16 | GAP-014 | AUTO-CLOSED | Autonomous doc sprint: 25 service specs |
| ITEM-17 | RISK-005 | **OWNER-REQUIRED** | CREDENTIAL: JWT_PRIVATE_KEY RSA key pair |
| ITEM-18 | RISK-009/R-001 | AUTO-CLOSED | Implementation sprint: R-001 DI refactor |
| ITEM-19 | RISK-010/R-004 | AUTO-CLOSED | Implementation sprint: R-004 model extraction |
| ITEM-20 | RISK-013 | AUTO-CLOSED | Testing Authority Capture: T-001 |
| ITEM-21 | NRM-R009 | **OWNER-REQUIRED** | PRODUCT POLICY: capability-resolution.md anchor |
| ITEM-22 | NRM-R010 | **OWNER-REQUIRED** | PRODUCT POLICY: doc-precedence.md anchor |

---

## Success Criteria Verification

| Criterion | Result |
|---|---|
| Every OWNER-REQUIRED item reviewed | ✅ 22 unique items, 41 handles |
| No technical-discovery item remains OWNER-REQUIRED | ✅ (GAP-012, GAP-013 → AUTO-CLOSED) |
| No UX-impacting item remains unresolved | ✅ All UX-affecting items have SAFE-DEFAULT |
| No current-scope implementation item unresolved | ✅ All sprint items have defaults |
| Remaining OWNER-REQUIRED items are genuine human decisions | ✅ (credential + protected anchor only) |

---

## Related Documents

- FINAL_CLASSIFIED_REGISTER.md — master classification
- UNRESOLVABLE_ITEMS_REGISTER.md — the 3 remaining OWNER-REQUIRED items
- DETERMINISM_CERTIFICATION_REPORT.md — certification of repository determinism
- BACKEND_GAP_REGISTER.md — updated with compression annotations
- AI_OPERATING_CONTEXT.md — D-001 through D-005 updated
- FEATURE_GAP_REGISTER.md — 6 FGAPs (unchanged by compression)
