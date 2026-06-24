# SAFE-DEFAULT REGISTER — PROJECT MEMORY LAYER

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: AI + Human

---

## Purpose

Contains every item resolved through a safe deterministic default. Each default is supported by repository evidence and can be reversed by the owner if needed. Implementation proceeds on the default path unless explicitly overridden.

Classification rule: SAFE-DEFAULT only if one path is overwhelmingly supported, implementation can proceed safely, and no commercial/legal risk is introduced.

---

## PM-SD-001: Checkout Persistence Timeline

| Field | Value |
|---|---|
| **Item ID** | PM-SD-001 |
| **Original ID** | ITEM-01 / PDC-001 / OC-001 / D-001 / R-005 / RISK-002 |
| **Title** | When should checkout-service receive SQLite persistence? |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — InMemoryCheckoutStore for dev; SQLiteCheckoutStore in persistence sprint |
| **Original Source** | AI_OPERATING_CONTEXT D-001; TBD-001; BACKEND_RISK_REGISTER RISK-002 |
| **Evidence Source** | checkout-service has no store_db.py; InMemoryCheckoutStore is active; BaseRepository pattern established in 16 other services |
| **Resolution Source** | Phase 2.95 PDC-001; OWNER-REQUIRED Compression ITEM-01; Phase 3.25 OC-001 PROCEEDED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Phase 2.95/3.25) — silence = acceptance |
| **Decision Summary** | Keep InMemoryCheckoutStore during development phase. Add store_db.py to checkout-service in the dedicated persistence sprint. Frontend checkout flow is contract-identical in both states. |
| **Detailed Explanation** | checkout-service manages checkout sessions, order items, and payment initiation. All data is currently in-memory (InMemoryCheckoutStore). On restart, all active checkout flows are lost. This is acceptable for development but is a CRITICAL risk for production. The fix is well-understood: add SQLiteCheckoutStore using the same BaseRepository pattern already established in 16 other services. The persistence sprint is the appropriate time to do this alongside the 53 other in-memory services. Frontend screens (SCR-019, /learner/checkout) are completely unaffected by which backend store is active. |
| **Affected Components** | checkout-service (backend/services/checkout-service/) |
| **Affected Routes** | /api/v1/checkout/* |
| **Affected APIs** | POST /api/v1/checkout/sessions, GET /api/v1/checkout/sessions/{id}, POST /api/v1/checkout/sessions/{id}/items, POST /api/v1/checkout/sessions/{id}/submit, POST /api/v1/checkout/sessions/{id}/initiate-payment, GET /api/v1/checkout/orders/{order_id} |
| **Affected Workflows** | WF-005 (JazzCash checkout) |
| **Affected Roles** | Learner (checkout), Admin (order management) |
| **Owner Required** | NO (default proceeds) |
| **External Dependency** | NO |
| **Future Impact** | HIGH — CRITICAL risk for production; must be resolved in persistence sprint before production launch |
| **Reopen Criteria** | Owner explicitly says "add persistence now" or production launch is imminent |
| **Default Reversal** | If reversed: add backend/services/checkout-service/app/store_db.py using SQLiteCheckoutStore extending BaseRepository. Wire into checkout-service main.py at startup. No frontend changes. |
| **Related Documents** | docs/08_reports/BACKEND_RISK_REGISTER.md RISK-002; docs/08_reports/BACKEND_GAP_REGISTER.md GAP-002; docs/08_reports/PRODUCT_DECISION_REGISTER.md PDC-001 |
| **Related Register Entries** | PM-SD-005 (53 services persistence sprint) |

---

## PM-SD-002: CI/CD and Cloud Deployment Target

| Field | Value |
|---|---|
| **Item ID** | PM-SD-002 |
| **Original ID** | ITEM-03 / PDC-002 / OC-002 / D-003 / R-013 |
| **Title** | Which cloud provider and CI/CD pipeline for production? |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — Docker Compose + GitHub Actions; cloud provider deferred |
| **Original Source** | AI_OPERATING_CONTEXT D-003; BACKEND_RISK_REGISTER R-013 |
| **Evidence Source** | infrastructure/deployment/docker-compose.yml confirmed active; infrastructure/ci-cd/deploy-backend.yml confirmed (GitHub Actions) |
| **Resolution Source** | Phase 2.95 PDC-002; Compression ITEM-03; Phase 3.25 OC-002 PROCEEDED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (silence = acceptance) |
| **Decision Summary** | Docker Compose for local development and staging. GitHub Actions for CI/CD. Cloud provider (AWS/GCP/Azure/DigitalOcean/self-hosted) selected at owner discretion when production deployment begins. |
| **Detailed Explanation** | The repository already contains a working Docker Compose setup (infrastructure/deployment/docker-compose.yml) and a GitHub Actions workflow (deploy-backend.yml). No cloud-specific SDK or configuration was found. Using what exists is the safe default. Cloud provider selection does not affect any current engineering work — frontend and backend are cloud-agnostic. |
| **Affected Components** | infrastructure/deployment/, infrastructure/ci-cd/ |
| **Affected Routes** | All (deployment affects everything) |
| **Affected APIs** | All |
| **Affected Workflows** | All (production deployment) |
| **Affected Roles** | DevOps (owner responsibility) |
| **Owner Required** | YES — for cloud provider selection (when production launch is planned) |
| **External Dependency** | YES — cloud provider account (see PM-ED-006) |
| **Future Impact** | HIGH — cloud choice affects cost, compliance, latency for Pakistan-first deployment |
| **Reopen Criteria** | Owner selects a cloud provider; production launch is scheduled |
| **Default Reversal** | When owner names a provider: update deploy-backend.yml with provider-specific steps (ECR/ECS for AWS, GCR/GKE for GCP, etc.) |
| **Related Documents** | infrastructure/deployment/docker-compose.yml; infrastructure/ci-cd/deploy-backend.yml |
| **Related Register Entries** | PM-ED-006 (cloud provider account) |

---

## PM-SD-003: File Upload API Endpoint

| Field | Value |
|---|---|
| **Item ID** | PM-SD-003 |
| **Original ID** | ITEM-06 / OC-003 / PDC-003 |
| **Title** | Which HTTP service owns the binary file upload endpoint? |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — content-service (metadata) + media-service (binary) |
| **Original Source** | AI_OPERATING_CONTEXT D-004a; FEATURE_SCOPE §1.3 |
| **Evidence Source** | content-service and media-service both in service-manifest.json. services/file-storage/service.py exists as domain library (not in manifest). |
| **Resolution Source** | Phase 2.95 PDC-003; Compression ITEM-06; Phase 3.25 OC-003 PROCEEDED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (silence = acceptance) |
| **Decision Summary** | content-service handles content metadata (title, description, type, duration). Binary upload (video, document, SCORM, image) targets media-service. Frontend FileUpload component renders with stub binary upload action until content sprint confirms endpoint. |
| **Detailed Explanation** | The services/file-storage/ domain library handles file storage business logic but is not registered as an HTTP service. Two HTTP services are candidates: content-service and media-service. The safe default splits responsibility: content-service for metadata (registration, tagging, search) and media-service for binary data (upload, transcoding, CDN delivery). This is the most common pattern in media-aware LMS platforms. |
| **Affected Components** | content-service, media-service |
| **Affected Routes** | /api/v1/content/*, /api/v1/media/* |
| **Affected APIs** | Content metadata CRUD; binary upload endpoint (TBD in content sprint) |
| **Affected Workflows** | WF-006 (content upload) |
| **Affected Roles** | Teacher (content creation), Admin (content management) |
| **Owner Required** | NO (default proceeds; reversal only if owner wants file-storage HTTP wrapper) |
| **External Dependency** | NO (binary storage; cloud bucket connection is a deployment concern) |
| **Future Impact** | MEDIUM — content sprint must define the binary upload endpoint shape |
| **Reopen Criteria** | Owner explicitly wants a new file-storage-service registered in manifest |
| **Default Reversal** | If reversed: add backend/services/file-storage/app/main.py (ASGI shim pattern); register in manifest; update FileUpload component target. |
| **Related Documents** | docs/08_reports/PRODUCT_DECISION_REGISTER.md PDC-003; docs/03_frontend_authority/FRONTEND_COMPONENT_INVENTORY.md (FileUpload component) |
| **Related Register Entries** | None |

---

## PM-SD-004: AI Tutor Scope Boundary

| Field | Value |
|---|---|
| **Item ID** | PM-SD-004 |
| **Original ID** | ITEM-07 / OC-004 / PDC-007 |
| **Title** | AI feature scope — confirmed services only or full copilot vision? |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — confirmed services in initial sprint; copilot overlay = FGAP-003 |
| **Original Source** | FEATURE_SCOPE §1.10 and §2; docs/designs/ai-learning-copilot.md |
| **Evidence Source** | service-manifest.json: ai-tutor-service, recommendation-service, skill-inference-service, course-generation-service — all confirmed. docs/designs/ai-learning-copilot.md — design doc for full copilot overlay. |
| **Resolution Source** | Phase 2.95 PDC-007; Compression ITEM-07; Phase 3.25 OC-004 PROCEEDED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (silence = acceptance) |
| **Decision Summary** | Initial sprint builds: ai-tutor chat panel (per-lesson), recommendations widget (learner dashboard), course generation UI (admin). Full AI copilot overlay (persistent cross-screen AI assistant) is deferred to AI copilot sprint (FGAP-003). |
| **Detailed Explanation** | The design document (ai-learning-copilot.md) describes a full copilot overlay — a persistent AI assistant appearing across all learner screens with cross-screen context awareness. The confirmed services (ai-tutor, recommendation, skill-inference, course-gen) support specific AI functions but not the full overlay. The safe default is to build to the confirmed services only and defer the overlay to a dedicated sprint where context-passing architecture can be designed. |
| **Affected Components** | ai-tutor-service, recommendation-service, skill-inference-service, course-generation-service |
| **Affected Routes** | /api/v1/ai-tutor/*, /api/v1/recommendations/*, /api/v1/courses/generate |
| **Affected APIs** | AI tutor, recommendation, course generation endpoints |
| **Affected Workflows** | WF-007 (AI tutoring); WF-008 (course generation) |
| **Affected Roles** | Learner (tutor + recommendations), Admin (course generation) |
| **Owner Required** | NO (default proceeds) |
| **External Dependency** | YES — Claude API or equivalent LLM API credentials for ai-tutor-service responses |
| **Future Impact** | HIGH — copilot overlay is a major UX differentiator; FGAP-003 sprint required |
| **Reopen Criteria** | Owner says "include full copilot in initial sprint" (triggers copilot overlay design sprint first) |
| **Default Reversal** | If reversed: additional copilot overlay design sprint before frontend builds cross-screen AI panel |
| **Related Documents** | docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-003; docs/designs/ai-learning-copilot.md |
| **Related Register Entries** | PM-OS-003 (FGAP-003 copilot overlay) |

---

## PM-SD-005: 53 Services In-Memory Persistence

| Field | Value |
|---|---|
| **Item ID** | PM-SD-005 |
| **Original ID** | ITEM-08 / GAP-002 / RISK-001 |
| **Title** | 53 backend services use in-memory storage — persistence sprint required |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — InMemory for dev; SQLite persistence sprint for all 53 |
| **Original Source** | BACKEND_GAP_REGISTER.md GAP-002; BACKEND_RISK_REGISTER.md RISK-001 |
| **Evidence Source** | Task 7 wired 16 services to SQLite. 53 remaining use InMemoryXStore. BaseRepository pattern established in shared/db/engine.py. Pattern is replicable. |
| **Resolution Source** | OWNER-REQUIRED Compression ITEM-08; Phase 3.25 confirmation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | SQLite is the confirmed persistence pattern (BaseRepository from shared/db/engine.py). Persistence sprint applies same pattern to all 53 remaining services. No new owner decision required. |
| **Detailed Explanation** | 16 services received SQLite stores in Task 7. The pattern is: (1) create store_db.py extending BaseRepository; (2) implement service-specific SQL schema and CRUD methods; (3) wire SQLiteXStore into main.py replacing InMemoryXStore. This pattern is proven, documented, and requires no architecture decision. The persistence sprint applies it at scale to the remaining 53 services. SQLite is the development/staging database. PostgreSQL migration is a future production concern (deferred commercial decision). |
| **Affected Components** | 53 backend services without store_db.py |
| **Affected Routes** | All routes of the 53 services |
| **Affected APIs** | All APIs of the 53 services |
| **Affected Workflows** | All workflows touching the 53 services |
| **Affected Roles** | All roles |
| **Owner Required** | NO for persistence sprint; YES for PostgreSQL migration timeline |
| **External Dependency** | NO (SQLite is stdlib) |
| **Future Impact** | CRITICAL — 53 services lose data on restart; must be resolved before production |
| **Reopen Criteria** | Owner requests PostgreSQL as dev database (changes the sprint scope) |
| **Default Reversal** | If owner wants PostgreSQL: update BaseRepository to use psycopg2/asyncpg; requires PostgreSQL deployment setup |
| **Related Documents** | docs/08_reports/BACKEND_GAP_REGISTER.md GAP-002; backend/services/shared/db/engine.py |
| **Related Register Entries** | PM-SD-001 (checkout-service specifically); PM-SD-008 (idempotency stores) |

---

## PM-SD-006: Cross-Process Message Queue — Kafka

| Field | Value |
|---|---|
| **Item ID** | PM-SD-006 |
| **Original ID** | ITEM-09 / GAP-003 / RISK-006 |
| **Title** | Cross-process event delivery — Kafka confirmed |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — Kafka integration sprint to wire EventBus to Kafka producer |
| **Original Source** | BACKEND_GAP_REGISTER.md GAP-003; EVENT_AND_QUEUE_ARCHITECTURE.md |
| **Evidence Source** | infrastructure/event-bus/event_bus_config.json: "platform": "kafka", cluster "lms-domain-events". 39 topics in event_topics.json. In-process EventBus already works for single-process delivery. |
| **Resolution Source** | OWNER-REQUIRED Compression ITEM-09; Phase 3.25 confirmation |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | Kafka is the confirmed cross-process message broker. Kafka integration sprint: wire EventBus.publish() to Kafka producer so events reach services in separate processes. |
| **Detailed Explanation** | The in-process EventBus (shared/events/bus.py) delivers events within a single OS process. Multi-service event delivery (e.g., enrollment.created reaching progress-service in a different process) requires Kafka. Kafka is already configured: event_bus_config.json specifies the platform, cluster name, and topic format. The Kafka integration sprint connects EventBus.publish() to a Kafka producer and wires subscribe() to a Kafka consumer group per service. In-process events continue to work in development without Kafka running. |
| **Affected Components** | backend/services/shared/events/bus.py, all services that publish or subscribe to events |
| **Affected Routes** | None directly (event-driven, not request-driven) |
| **Affected APIs** | None directly |
| **Affected Workflows** | All event-driven workflow steps (post-enrollment events, post-payment events, etc.) |
| **Affected Roles** | System (automated event processing) |
| **Owner Required** | NO for Kafka integration; YES for Kafka cluster provisioning in production |
| **External Dependency** | YES — Kafka cluster (cloud-managed or self-hosted) for production |
| **Future Impact** | HIGH — cross-service workflows cannot scale without Kafka; single-process works for MVP demo |
| **Reopen Criteria** | Owner decides to use a different broker (RabbitMQ, Redis Streams, NATS) |
| **Default Reversal** | If reversed: update event_bus_config.json platform; implement broker-specific adapter |
| **Related Documents** | infrastructure/event-bus/event_bus_config.json; infrastructure/event-bus/event_topics.json; backend/services/shared/events/ |
| **Related Register Entries** | PM-AC-041 (WF-001 onboarding — no events); PM-AC-042 (WF-005 JazzCash — domain events) |

---

## PM-SD-007: auth-service Spec Drift Update

| Field | Value |
|---|---|
| **Item ID** | PM-SD-007 |
| **Original ID** | ITEM-11 / GAP-009 |
| **Title** | auth-service-spec.md defines spec entities not matching SQLite implementation |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — update auth-service-spec.md in doc sprint |
| **Original Source** | BACKEND_GAP_REGISTER.md GAP-009 |
| **Evidence Source** | auth-service/app/store_db.py — 7 tables: auth_tenants, auth_user_credentials, auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events |
| **Resolution Source** | OWNER-REQUIRED Compression ITEM-11 |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | Update auth-service-spec.md to document the actual 7-table SQLite implementation. No owner decision required — spec must match implementation. |
| **Detailed Explanation** | auth-service-spec.md describes entities (refresh_token_family, login_audit_event, key_metadata) that don't match the actual implementation. The SQLite implementation has 7 concrete tables. The spec update is a documentation task — autonomous per REVISED_DECISION_ESCALATION_MATRIX. Spec update sprint: open auth-service-spec.md, replace entity descriptions with the 7 confirmed tables and their schemas. |
| **Affected Components** | docs/specs/auth-service-spec.md |
| **Affected Routes** | None (documentation only) |
| **Affected APIs** | None directly (spec documents the API) |
| **Affected Workflows** | None |
| **Affected Roles** | None |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | LOW — stale spec confuses future developers; doc sprint resolves |
| **Reopen Criteria** | Never (doc update is one-time; only re-opens if schema changes) |
| **Related Documents** | docs/specs/auth-service-spec.md; backend/services/auth-service/app/store_db.py |
| **Related Register Entries** | PM-AC-034 (TBD-006 refresh token family); PM-AC-035 (TBD-007 login response shape) |

---

## PM-SD-008: SQLite Idempotency Stores

| Field | Value |
|---|---|
| **Item ID** | PM-SD-008 |
| **Original ID** | ITEM-12 / GAP-010 / RISK-007 |
| **Title** | Idempotency stores reset on service restart — protection lost |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — SQLiteIdempotencyStore in persistence sprint |
| **Original Source** | BACKEND_GAP_REGISTER.md GAP-010; BACKEND_RISK_REGISTER.md RISK-007 |
| **Evidence Source** | progress-service and checkout-service use InMemoryIdempotencyStore. Keys lost on restart. |
| **Resolution Source** | OWNER-REQUIRED Compression ITEM-12 |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | Add SQLiteIdempotencyStore to checkout-service in persistence sprint. Same BaseRepository pattern. |
| **Detailed Explanation** | Idempotency keys prevent duplicate request processing (e.g., double-charge on network retry). If the store resets on restart, a duplicate request arriving after restart bypasses protection. The fix is straightforward: SQLiteIdempotencyStore with a TTL column. Include this in the persistence sprint alongside checkout-service SQLite store (PM-SD-001). |
| **Affected Components** | checkout-service, progress-service |
| **Affected Routes** | POST /api/v1/checkout/sessions, POST /api/v1/progress/* |
| **Affected APIs** | Checkout and progress endpoints with idempotency keys |
| **Affected Workflows** | WF-005 (checkout), WF-004 (progress) |
| **Affected Roles** | Learner |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | HIGH — duplicate charges possible in production without persistent idempotency |
| **Reopen Criteria** | Never (standard fix; only re-opens if different idempotency approach is chosen) |
| **Related Documents** | docs/08_reports/BACKEND_GAP_REGISTER.md GAP-010 |
| **Related Register Entries** | PM-SD-001 (checkout persistence) |

---

## PM-SD-009: Pagination Total Stub

| Field | Value |
|---|---|
| **Item ID** | PM-SD-009 |
| **Original ID** | ITEM-13 / GAP-011 |
| **Title** | enrollment-service list pagination returns stub total (len(items) not COUNT(*)) |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — implement COUNT(*) in persistence sprint |
| **Original Source** | BACKEND_GAP_REGISTER.md GAP-011 |
| **Evidence Source** | enrollment-service/app/service.py — comment: "# stub total; real impl would query count separately" |
| **Resolution Source** | OWNER-REQUIRED Compression ITEM-13 |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI (Compression phase) |
| **Decision Summary** | Implement SELECT COUNT(*) FROM enrollments WHERE tenant_id=? in enrollment-service list handler. Standard SQL; no architecture decision. |
| **Detailed Explanation** | Frontend pagination requires accurate total counts. The stub returns len(in-memory list) which becomes inaccurate at scale with DB-backed storage. Fix: add count query to enrollment-service list endpoint. This is part of the SQLite persistence sprint when enrollment-service DB store is confirmed active. |
| **Affected Components** | enrollment-service |
| **Affected Routes** | GET /api/v1/enrollments?page=&per_page= |
| **Affected APIs** | Enrollment list endpoint |
| **Affected Workflows** | WF-003 (enrollment management) |
| **Affected Roles** | Admin (enrollment management), Learner (course list) |
| **Owner Required** | NO |
| **External Dependency** | NO |
| **Future Impact** | MEDIUM — inaccurate pagination on large datasets; acceptable for early users |
| **Reopen Criteria** | Never (standard SQL fix) |
| **Related Documents** | docs/08_reports/BACKEND_GAP_REGISTER.md GAP-011 |
| **Related Register Entries** | PM-SD-005 (persistence sprint) |

---

## PM-SD-010: File-Storage HTTP Layer Pattern

| Field | Value |
|---|---|
| **Item ID** | PM-SD-010 |
| **Original ID** | PDC-003 (additional detail) |
| **Title** | Content upload: FileUpload component uses stub until content sprint |
| **Classification** | SAFE-DEFAULT |
| **Current Status** | DEFAULT APPLIED — FileUpload renders with stub binary endpoint |
| **Original Source** | PRODUCT_DECISION_REGISTER.md PDC-003 |
| **Evidence Source** | FRONTEND_COMPONENT_INVENTORY.md — FileUpload component defined; binary endpoint is stub |
| **Resolution Source** | Phase 2.95 PDC-003; Phase 3.25 OC-003 PROCEEDED |
| **Resolution Date** | 2026-06-23 |
| **Resolved By** | AI |
| **Decision Summary** | FileUpload component is built and renders. Binary upload API endpoint is a stub (POST /api/v1/media/upload or equivalent) until content sprint confirms exact endpoint. |
| **Detailed Explanation** | Frontend FileUpload component is complete as a reusable component. The backend binary upload endpoint is undefined (content sprint work). The stub allows the component to render in content management screens. The stub returns a mock upload response in development. Content sprint wires the real endpoint. |
| **Affected Components** | FileUpload component (frontend); content-service, media-service (backend) |
| **Affected Routes** | /admin/courses/:id/content (content management screens) |
| **Affected APIs** | POST /api/v1/media/upload (stub — to be confirmed in content sprint) |
| **Affected Workflows** | WF-006 (content upload) |
| **Affected Roles** | Teacher (content upload), Admin (content management) |
| **Owner Required** | NO |
| **External Dependency** | NO (for dev; cloud bucket for production binary storage) |
| **Future Impact** | MEDIUM — content sprint must define and implement binary upload endpoint |
| **Reopen Criteria** | Content sprint begins |
| **Related Documents** | docs/03_frontend_authority/FRONTEND_COMPONENT_INVENTORY.md |
| **Related Register Entries** | PM-SD-003 (file upload API endpoint) |

---

## Safe-Default Reversal Protocol

Any SAFE-DEFAULT item can be reversed by the owner. Reversal process:

1. Owner states the reversal explicitly: "reverse [PM-SD-NNN]" or equivalent
2. AI identifies affected items in this register
3. AI identifies all affected code files (services, specs, components)
4. AI executes the reversal in a dedicated session
5. This register entry is updated: STATUS = REVERSED; new path documented

No SAFE-DEFAULT reversal requires a new governance phase. It is an implementation sprint task.
