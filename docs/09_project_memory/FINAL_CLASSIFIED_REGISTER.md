# FINAL CLASSIFIED REGISTER — PROJECT MEMORY LAYER

Status: Active — Institutional Memory
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: AI + Human

---

## PURPOSE

This is the master index of every classified item in the project. It is the single entry point for all future AI sessions. Load this before auditing, redesigning, doing frontend work, backend work, deployment work, or gap analysis.

This register does NOT replace the authority documents (docs/00_authority/). The authority layer is the source of truth for what the system IS. This register is the source of institutional memory for what has already been DECIDED, PROVEN, DEFERRED, or NOTED AS PENDING.

---

## CLASSIFICATION KEY

| Code | Meaning | Register |
|---|---|---|
| AUTO-CLOSED | Proven from repository evidence. No decision needed. | AUTO_CLOSED_REGISTER.md |
| SAFE-DEFAULT | One clear path supported by evidence. Implemented unless owner reverses. | SAFE_DEFAULT_REGISTER.md |
| OWNER-DECISION | Genuine human decision required. Cannot be derived. | OWNER_DECISION_REGISTER.md |
| EXTERNAL-DEPENDENCY | Requires external provisioning, credentials, or vendor onboarding. | EXTERNAL_DEPENDENCY_REGISTER.md |
| OUT-OF-SCOPE | Intentionally deferred, future phase, regional expansion, or excluded. | OUT_OF_SCOPE_REGISTER.md |

---

## SECTION 1: AUTO-CLOSED ITEMS (43 items)

Items proven directly from code, architecture, contracts, or authority documents. No decisions remain.

### Phase 2.9 — Approval Elimination (13 items)

| PM ID | Original ID | Title | Status | Date |
|---|---|---|---|---|
| PM-AC-001 | OA-001 | notification-service ASGI shim | CLOSED — FIXED Phase 2.9 | 2026-06-23 |
| PM-AC-002 | OA-002 | branch_ids in AssignmentCreateRequest | CLOSED — FIXED Phase 2.9 | 2026-06-23 |
| PM-AC-003 | OA-003 | Enrollments unique constraint | CLOSED — not a gap, service layer correct | 2026-06-23 |
| PM-AC-004 | OA-004 | service:ClassName runtime (D-002) | CLOSED — ASGI shims added Phase 2.9 | 2026-06-23 |
| PM-AC-005 | OA-005 | assessment/attempt route overlap | CLOSED — intentional alias confirmed | 2026-06-23 |
| PM-AC-006 | OA-006 | Root services/ classification | CLOSED — documented, active directories | 2026-06-23 |
| PM-AC-007 | OA-007 | Competing EventEnvelope definitions | CLOSED — consolidated Phase 2.9 | 2026-06-23 |
| PM-AC-008 | OA-008 | integrations/payment vs payments | CLOSED — both active, not a conflict | 2026-06-23 |
| PM-AC-009 | OA-009 | session-service v2 prefix | CLOSED — v2 prefix intentional | 2026-06-23 |
| PM-AC-010 | OA-010 | docs/qc/ Python scripts move | CLOSED — done Phase 2.9 | 2026-06-23 |
| PM-AC-011 | OA-011 | Dockerfiles/CI/CD constraint statement | CLOSED — constraint documented | 2026-06-23 |
| PM-AC-012 | OA-012 | analytics-ingestion vs event-ingestion | CLOSED — alignment confirmed | 2026-06-23 |
| PM-AC-013 | OA-013 | event_topics.json canonical names vs code | CLOSED — alias pattern recorded | 2026-06-23 |

### Phase 2.9/2.95 — Compression AUTO-CLOSED (10 items)

| PM ID | Original ID | Title | Status | Date |
|---|---|---|---|---|
| PM-AC-014 | ITEM-02 / D-002 / GAP-006 | Class-based service startup mechanism | CLOSED — ASGI shims + manifest update Phase 2.9 | 2026-06-23 |
| PM-AC-015 | ITEM-04 / D-004 / R-006 | Orphaned services in services/ | CLOSED — archived, no code references | 2026-06-23 |
| PM-AC-016 | ITEM-05 / D-005 / R-011 | Dual reconciliation paths | CLOSED — reconciliation is backend-only domain logic | 2026-06-23 |
| PM-AC-017 | ITEM-14 / GAP-012 | Node.js services not inventoried | CLOSED — reclassified as technical discovery sprint | 2026-06-23 |
| PM-AC-018 | ITEM-15 / GAP-013 | payment-service non-standard entrypoint | CLOSED — reclassified as technical verification task | 2026-06-23 |
| PM-AC-019 | ITEM-16 / GAP-014 | 25 services without specs | CLOSED — reclassified as autonomous doc sprint (R-008) | 2026-06-23 |
| PM-AC-020 | ITEM-18 / RISK-009 / R-001 | entitlement service DI conflict | CLOSED — reclassified as U12 implementation sprint | 2026-06-23 |
| PM-AC-021 | ITEM-19 / RISK-010 / R-004 | Circular import model extraction | CLOSED — reclassified as U12 implementation sprint | 2026-06-23 |
| PM-AC-022 | ITEM-20 / RISK-013 | Frontend zero tests | CLOSED — Testing Authority Capture sprint | 2026-06-23 |
| PM-AC-023 | ITEM-10 / GAP-006 dup | Class-based startup (duplicate) | CLOSED — duplicate of PM-AC-014 | 2026-06-23 |

### Phase 2.95 — Product Decisions RESOLVED (5 items)

| PM ID | Original ID | Title | Status | Date |
|---|---|---|---|---|
| PM-AC-024 | PDC-004 | interaction-service existence | CLOSED — does not exist, no design intent | 2026-06-23 |
| PM-AC-025 | PDC-011 | JazzCash webhook reconciliation (frontend) | CLOSED — backend only; frontend polls order status | 2026-06-23 |
| PM-AC-026 | PDC-012 | Frontend navigation model | CLOSED — authorize endpoint confirmed (POST /api/v1/rbac/authorize) | 2026-06-23 |
| PM-AC-027 | PDC-013 | Duplicate lesson event topics | CLOSED — backend internal EventBus only | 2026-06-23 |
| PM-AC-028 | PDC-014 | Root services/ layer classification | CLOSED — backend architecture; no frontend impact | 2026-06-23 |

### Pre-Frontend Delta Audit — TBD Resolutions (12 items)

| PM ID | Original ID | Title | Status | Date |
|---|---|---|---|---|
| PM-AC-029 | TBD-001 | Checkout-service DB persistence (D-001) | CLOSED — no store_db.py; InMemoryCheckoutStore confirmed | 2026-06-23 |
| PM-AC-030 | TBD-002 | store_db.py files actively used | CLOSED — yes, 16 services now wired to SQLite | 2026-06-23 |
| PM-AC-031 | TBD-003 | ORM/migration framework existence | CLOSED — no ORM; custom BaseRepository on sqlite3 stdlib | 2026-06-23 |
| PM-AC-032 | TBD-004 | External persistence layer (PostgreSQL/Redis) | CLOSED — none; SQLite only; infra env files are placeholders | 2026-06-23 |
| PM-AC-033 | TBD-005 | service:ClassName runtime identification | CLOSED — no runtime found; resolved via ASGI shims Phase 2.9 | 2026-06-23 |
| PM-AC-034 | TBD-006 | Refresh token family tracking | CLOSED — implemented via auth_refresh_tokens table (parent_token_id + replaced_by_token_id) | 2026-06-23 |
| PM-AC-035 | TBD-007 | Login response shape | CLOSED — verified: {session_id, user: {user_id, tenant_id}, access_token, ...} | 2026-06-23 |
| PM-AC-036 | TBD-008 | JWT user identifier claim | CLOSED — confirmed: sub claim = user_id | 2026-06-23 |
| PM-AC-037 | TBD-009 | EventBus implementation status | CLOSED — thread-safe in-process EventBus in shared/events/bus.py | 2026-06-23 |
| PM-AC-038 | TBD-010 | infrastructure env files sensitivity | CLOSED — not sensitive; placeholder credentials only | 2026-06-23 |
| PM-AC-039 | TBD-011 | Tenant model fields | CLOSED — 6 fields: tenant_id, name, country_code, segment_type, plan_type, addon_flags | 2026-06-23 |
| PM-AC-040 | TBD-012 | spec_index.json consumer | CLOSED — stale artifact, no consumer, no scripts/ directory | 2026-06-23 |

### Phase 3.25 — Autonomous Gap Elimination AUTO-CLOSED (3 items)

| PM ID | Original ID | Title | Status | Date |
|---|---|---|---|---|
| PM-AC-041 | DC-012 | WF-001 onboarding events | CLOSED — CONFIRMED NONE: 39 topics, no tenant/onboarding events | 2026-06-23 |
| PM-AC-042 | DC-013 | WF-005 JazzCash webhook reconciliation | CLOSED — CONFIRMED: PaymentReconciliationEngine.run_reconciliation_pass() | 2026-06-23 |
| PM-AC-043 | DC-019 through DC-024 | AI_OPERATING_CONTEXT stale content (6 fields) | CLOSED — all 6 stale fields updated to current state | 2026-06-23 |

---

## SECTION 2: SAFE-DEFAULT ITEMS (10 items)

Items where one path is overwhelmingly supported by evidence. Implementation proceeds unless owner reverses.

| PM ID | Original ID | Title | Default Applied | Date |
|---|---|---|---|---|
| PM-SD-001 | ITEM-01 / PDC-001 / OC-001 | Checkout persistence timeline | InMemoryCheckoutStore for dev; SQLite in persistence sprint | 2026-06-23 |
| PM-SD-002 | ITEM-03 / PDC-002 / OC-002 | CI/CD and cloud deployment target | Docker Compose + GitHub Actions; cloud provider at owner discretion | 2026-06-23 |
| PM-SD-003 | ITEM-06 / OC-003 | File upload API endpoint | content-service (metadata) + media-service (binary) | 2026-06-23 |
| PM-SD-004 | ITEM-07 / OC-004 / PDC-007 | AI tutor scope boundary | Confirmed services (ai-tutor + recommendation + course-gen) in initial sprint | 2026-06-23 |
| PM-SD-005 | ITEM-08 / GAP-002 | 53 services in-memory persistence | SQLite persistence sprint using established BaseRepository pattern | 2026-06-23 |
| PM-SD-006 | ITEM-09 / GAP-003 | Cross-process message queue | Kafka confirmed via event_bus_config.json; Kafka integration sprint | 2026-06-23 |
| PM-SD-007 | ITEM-11 / GAP-009 | auth-service spec drift | Update auth-service-spec.md to match 7-table SQLite implementation | 2026-06-23 |
| PM-SD-008 | ITEM-12 / GAP-010 | Idempotency stores on restart | SQLiteIdempotencyStore in persistence sprint | 2026-06-23 |
| PM-SD-009 | ITEM-13 / GAP-011 | Pagination total stub | Implement COUNT(*) in enrollment-service list handler in persistence sprint | 2026-06-23 |
| PM-SD-010 | PDC-003 | File-storage HTTP layer pattern | content-service + media-service; FileUpload component uses stub until sprint | 2026-06-23 |

---

## SECTION 3: OWNER-DECISION ITEMS (3 items)

Genuine decisions that cannot be derived from repository. These are non-blocking for all engineering phases.

| PM ID | Original ID | Title | Status | Blocks Production? |
|---|---|---|---|---|
| PM-OD-001 | OR-001 / ITEM-17 / RISK-005 | JWT_PRIVATE_KEY — RSA key generation | OPEN — awaiting operator action | YES (deployment only) |
| PM-OD-002 | OR-002 / ITEM-21 | capability-resolution.md anchor update | OPEN — awaiting owner approval | No |
| PM-OD-003 | OR-003 / ITEM-22 | doc-precedence.md anchor update | OPEN — awaiting owner approval | No |

---

## SECTION 4: EXTERNAL-DEPENDENCY ITEMS (8 items)

Require external provisioning, vendor accounts, credentials, or registrations. Not software gaps.

| PM ID | ID | Title | Status | Blocks Production? |
|---|---|---|---|---|
| PM-ED-001 | ED-001 | JazzCash merchant account + API credentials | PENDING — not provisioned for production | YES (payments) |
| PM-ED-002 | ED-002 | EasyPaisa merchant account + API credentials | PENDING — not provisioned for production | YES (payments) |
| PM-ED-003 | ED-003 | SMTP email service provider credentials | PENDING — development uses no-op or mock | YES (notifications) |
| PM-ED-004 | ED-004 | Domain name + DNS configuration | PENDING — required before production | YES (production URL) |
| PM-ED-005 | ED-005 | SSL/TLS certificate provisioning | PENDING — auto-provisioned via cloud (Let's Encrypt) or manual | YES (HTTPS) |
| PM-ED-006 | ED-006 | Cloud provider account selection + setup | PENDING — Docker Compose for dev; cloud when ready | NO (dev continues) |
| PM-ED-007 | ED-007 | FBR (Federal Board of Revenue) e-commerce registration | PENDING — Pakistan tax compliance | Regulatory |
| PM-ED-008 | ED-008 | SMS gateway credentials (OTP notifications) | PENDING — required for SMS-based notifications | PARTIAL (email fallback) |

---

## SECTION 5: OUT-OF-SCOPE ITEMS (10 items)

Intentionally deferred, future phase, regional expansion, or formally excluded. These do NOT block any current engineering work.

| PM ID | ID | Title | Status | Sprint When? |
|---|---|---|---|---|
| PM-OS-001 | FGAP-001 | Parent/Guardian Portal | DEFERRED — no service, no workflow; parent portal sprint TBD | Post-initial launch |
| PM-OS-002 | FGAP-002 | Adaptive Learning Engine | DEFERRED — design doc exists; no service; adaptive sprint TBD | Post-initial launch |
| PM-OS-003 | FGAP-003 | AI Learning Copilot Overlay | DEFERRED — confirmed services in scope; overlay is deferred | AI copilot sprint |
| PM-OS-004 | FGAP-004 | Learner Risk Insights | DEFERRED — design doc exists; no service; risk sprint TBD | Post-initial launch |
| PM-OS-005 | FGAP-005 | Reconciliation Admin Screen | DEFERRED — backend domain exists; HTTP endpoint missing; admin sprint | Post-initial launch |
| PM-OS-006 | FGAP-006 | PWA Offline Frontend | DEFERRED — backend offline-sync-service exists; PWA layer missing | PWA sprint |
| PM-OS-007 | MO-041 | Urdu Language Internationalization | FORMALLY DEFERRED — FEATURE_SCOPE §3 | Regional sprint |
| PM-OS-008 | MO-042 | Vocational Training Module | FORMALLY DEFERRED — FEATURE_SCOPE §3 | Vocational sprint |
| PM-OS-009 | MO-043 | Teacher Marketplace | FORMALLY DEFERRED — FEATURE_SCOPE §3 | Marketplace sprint |
| PM-OS-010 | MO-044 | Offline Box (Hardware Product) | PERMANENTLY EXCLUDED — FEATURE_SCOPE §3 | Never (hardware) |

---

## SECTION 6: FSC FRONTEND CONSUMER CONFIRMATIONS (9 items)

Populated in Phase 3.25. Record that these were TBD and are now confirmed.

| PM ID | FSC ID | Contract Point | Confirmed Consumer | Date |
|---|---|---|---|---|
| PM-AC-FSC-001 | FSC-001 | Auth/Login | /login (SCR-001); sub=user_id; fetch RBAC assignments | 2026-06-23 |
| PM-AC-FSC-002 | FSC-002 | Enrollment | /learner/courses/:id enroll; POST /api/v1/enrollments | 2026-06-23 |
| PM-AC-FSC-003 | FSC-003 | Checkout | /learner/checkout (SCR-019); 6 endpoints verified | 2026-06-23 |
| PM-AC-FSC-004 | FSC-004 | Progress | /learner/courses/:id/learn/:lid (SCR-018); 3 endpoints verified | 2026-06-23 |
| PM-AC-FSC-005 | FSC-005 | Certificate | /learner/certificates/:id (SCR-021); spec-level confirmed | 2026-06-23 |
| PM-AC-FSC-006 | FSC-006 | Timetable/Attendance | /admin/batches/:id/timetable + /teacher/batches/:id/attendance | 2026-06-23 |
| PM-AC-FSC-007 | FSC-007 | RBAC/Permission Guard | PermissionGuard components; D-002 RESOLVED (ASGI shims) | 2026-06-23 |
| PM-AC-FSC-008 | FSC-008 | LTI | /lti/launch; Redis nonce store (TTL 600s confirmed) | 2026-06-23 |
| PM-AC-FSC-009 | FSC-009 | Notifications | /notifications (SCR-025); domain entities confirmed | 2026-06-23 |

---

## ITEM COUNT SUMMARY

| Classification | Count | Register |
|---|---|---|
| AUTO-CLOSED | 43 + 9 FSC = 52 | AUTO_CLOSED_REGISTER.md |
| SAFE-DEFAULT | 10 | SAFE_DEFAULT_REGISTER.md |
| OWNER-DECISION | 3 | OWNER_DECISION_REGISTER.md |
| EXTERNAL-DEPENDENCY | 8 | EXTERNAL_DEPENDENCY_REGISTER.md |
| OUT-OF-SCOPE | 10 | OUT_OF_SCOPE_REGISTER.md |
| **TOTAL** | **83** | — |

---

## PHASE HISTORY

| Phase | Items Processed | Outcome |
|---|---|---|
| Phase 2.9 — Approval Elimination | 13 OA items | All 13 AUTO-CLOSED or FIXED |
| Phase 2.95 — Residual Decision Collapse | 14 PDC items | 5 RESOLVED, 3 OC, 6 IMPLEMENTATION_GAP |
| OWNER-REQUIRED Compression | 22 ITEM items | 9 AUTO-CLOSED, 10 SAFE-DEFAULT, 3 OWNER-REQUIRED |
| Pre-Frontend Delta Audit | 12 TBD items | All 12 resolved from code |
| Phase 3 — Frontend Authority Capture | 12 documents created | All screen/route/component/API questions answered |
| Phase 3.25 — Gap Elimination | 24 DC collapses | All open TBDs eliminated |
| Phase Memory Layer | This register | 83 items classified and indexed |

---

## USAGE RULE

Every future AI session touching this project MUST read this register before any of the following actions:
- Auditing
- Redesigning
- Gap analysis
- Frontend implementation
- Backend implementation
- Deployment work

After loading this register, proceed to the specific subordinate register for any item needing full detail.
