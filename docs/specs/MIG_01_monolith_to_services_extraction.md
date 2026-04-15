# MIG_01 — Monolith to Services Extraction Plan (Rails LMS -> Enterprise LMS V2)

## 0. Objective and Constraints

This plan defines a safe, incremental extraction from the current Rails LMS monolith to Enterprise LMS V2 service boundaries while preserving runtime continuity for:

- `User`
- `Course`
- `Lesson`
- `Enrollment`
- `Progress`
- `Certificate`

Non-negotiable migration rules in this plan:

1. Rails monolith is source of truth (SoT) at start.
2. Extraction is incremental (no big-bang).
3. No duplicate SoT ownership.
4. Every extracted service has explicit ownership.
5. API/event interception is used for safe transition.
6. Backward compatibility is preserved.
7. `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate` remain functional at all times.
8. Tenant/analytics extensions are introduced safely.
9. AI services come only after core runtime stabilization.
10. No circular dependencies between monolith and extracted services.

---

## 1. Migration Strategy

### 1.1 Operating model

- Use a **Strangler Fig** approach: keep monolith endpoints stable, introduce an edge compatibility layer, then route specific capabilities to extracted services once each is ready.
- Use **single-writer ownership transfer** per domain:
  - Before cutover: monolith writes, service is read shadow/projection.
  - At cutover: one-time ownership switch.
  - After cutover: service writes; monolith reads via adapter.
- Use **contract-first APIs + canonical domain events**.
- Use **idempotent consumers**, **outbox pattern**, and **versioned schemas** for reliability.

### 1.2 Safety controls

- Feature flags per service and per endpoint.
- Dark reads and shadow traffic before write cutover.
- SLO gates: latency, error rate, data parity, event lag.
- Rollback playbooks pre-approved for every extraction step.

---

## 2. Service Extraction Order (Required Sequence)

### Phase A
1. `auth_service`
2. `user_service`
3. `rbac_service`

### Phase B
4. `tenant_service`
5. `institution_service`

### Phase C
6. `course_service`
7. `lesson_service`
8. `enrollment_service`
9. `progress_service`
10. `certificate_service`

### Phase D
11. `program_service`
12. `cohort_service`
13. `session_service`
14. `assessment_service`

### Phase E
15. `event_ingestion_service`
16. `learning_analytics_service`

### Phase F
17. `ai_tutor_service`
18. `recommendation_service`
19. `skill_inference_service`

Dependency policy:
- A service may depend only on services in the same phase if explicitly declared and acyclic, or earlier phases.
- AI services (Phase F) are read-mostly and extension-only at launch.

---

## 3. Monolith-to-Service Boundary Mapping

| Monolith Runtime Entity / Module | Target Owner Service | Notes |
|---|---|---|
| Authentication flows, credentials, token issuance | `auth_service` | Identity proof + token lifecycle only. |
| `User` profile lifecycle | `user_service` | Canonical person profile ownership post-cutover. |
| Role/permission policy logic | `rbac_service` | Authorization policy decisions only. |
| Tenant context + partition keys | `tenant_service` | Global tenancy boundary + tenant metadata. |
| Institution hierarchy + institution metadata | `institution_service` | Org metadata and membership links. |
| `Course` core lifecycle | `course_service` | `Course` SoT in Phase C. |
| `Lesson` core lifecycle | `lesson_service` | Lesson authored runtime records. |
| `Enrollment` status/lifecycle | `enrollment_service` | Enrollment activation/withdrawal/completion state. |
| `Progress` tracking and completion projections | `progress_service` | Progress percentages, statuses, activity timestamps. |
| `Certificate` issuance/verification metadata | `certificate_service` | Credential records + provenance links. |
| Program composition / learning paths | `program_service` | Cross-course grouping. |
| Cohort grouping + membership | `cohort_service` | Cohort operations. |
| Session scheduling/attendance | `session_service` | Instructor-led runtime sessions. |
| Assessment attempts/results | `assessment_service` | Tests/quizzes/grades boundary. |
| Event normalization/relay | `event_ingestion_service` | Broker ingress + schema governance. |
| Analytical marts/features | `learning_analytics_service` | Non-SoT analytical projections. |
| AI tutoring | `ai_tutor_service` | Non-authoritative recommendations/guidance. |
| Recommendations | `recommendation_service` | Non-authoritative ranking/suggestions. |
| Skill inference | `skill_inference_service` | Non-authoritative inferred skill graph. |

---

## 4. Data Ownership Transition Plan

Ownership transitions use five states:

1. **State 0 – Monolith SoT**: Service has no write path.
2. **State 1 – Projection**: Service receives replicated data/events for read validation.
3. **State 2 – Shadow Read**: Edge compares monolith and service reads.
4. **State 3 – Write Cutover**: Single writer flips to service.
5. **State 4 – Monolith Adapter**: Monolith calls service APIs; monolith DB tables become legacy/read-only.

Rules:
- Never dual-write business entities from both sides.
- During State 3, perform bounded freeze window + checkpointed migration job.
- Every ownership switch has explicit runbook and rollback point.

---

## 5. API Strangler Pattern Plan

### 5.1 Compatibility edge

Introduce `lms_compat_gateway` in front of monolith/service APIs:
- Routes legacy URIs unchanged for clients.
- Performs route-by-capability to monolith or extracted service.
- Adds correlation IDs, tenant headers, auth context.

### 5.2 Routing progression per capability

- Step 1: Pass-through to monolith.
- Step 2: Mirror read to service (shadow compare, no client impact).
- Step 3: Canary route % traffic to service read endpoints.
- Step 4: Route writes to service after SoT cutover.
- Step 5: Keep monolith adapter endpoint for rollback only until decommission checkpoint.

### 5.3 Backward compatibility

- Preserve legacy response envelopes until client migrations complete.
- Use API versioning (`v1 legacy`, `v2 service-native`), with compatibility transforms at gateway.

---

## 6. Event Introduction Plan

### 6.1 Event backbone

- Introduce canonical event contracts early (Phase A/B infra prep):
  - `user.created|updated|status_changed`
  - `course.created|updated|published`
  - `lesson.created|updated|published`
  - `enrollment.created|status_changed`
  - `progress.updated|completed`
  - `certificate.issued|revoked`

### 6.2 Reliability pattern

- Monolith outbox table first, then service outboxes after cutovers.
- CDC/outbox dispatcher publishes to broker.
- Consumers are idempotent, schema-version aware.
- Dead-letter queues + replay tooling.

### 6.3 Event adoption order

1. Produce monolith events (authoritative).
2. Services consume and build projections.
3. After service ownership transfer, service becomes authoritative producer for that domain.
4. Monolith consumes those events for legacy reads until decommission.

---

## 7. Database Migration Plan

### 7.1 Principles

- Start with monolith DB authoritative.
- Create service databases per bounded context.
- Use one-time historical backfill + continuous CDC until cutover.
- Validate counts, checksums, semantic parity.

### 7.2 Checkpoints

1. **Schema Readiness**: Service DB schemas + constraints deployed.
2. **Historical Backfill Complete**: Full snapshot loaded and reconciled.
3. **CDC Healthy**: Replication lag < threshold.
4. **Parity Verified**: Record counts + key business invariants match.
5. **Write Cutover**: Single-writer switch.
6. **Legacy Freeze**: Monolith tables set read-only for moved domains.

### 7.3 Runtime entities safeguard

For `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`:
- Cut over one entity owner at a time in Phase C.
- Keep cross-entity foreign-reference checks via APIs/events (not cross-DB joins).

---

## 8. Rollback Strategy

Rollback levels:

1. **Route rollback**: Gateway routes all traffic back to monolith.
2. **Write rollback**: Disable service writes via feature flag, resume monolith write path if ownership not irreversibly switched.
3. **Data rollback**: Use checkpoint snapshots and event replay to restore pre-cutover state.
4. **Consumer rollback**: Pause event consumers, replay from last good offset.

Rules:
- No destructive schema/table drops until two release cycles after stable cutover.
- Rollback SLA < 30 minutes for route rollback; < 2 hours for write/data rollback.

---

## 9. Coexistence Model (Monolith + Services)

### 9.1 Coexistence architecture

- Monolith remains active for non-extracted domains.
- Extracted services own their domains and expose APIs/events.
- Gateway handles routing and payload adaptation.
- Event bus synchronizes state across legacy and new boundaries.

### 9.2 Anti-circular dependency rules

- Monolith may call extracted services through gateway adapters.
- Extracted services must **not** call monolith business endpoints synchronously for core writes.
- Service-to-service calls follow dependency direction of extraction order only.

### 9.3 Operational model

- Unified observability (trace IDs across monolith and services).
- Per-service error budgets and rollout gates.
- Incident response runbooks updated per phase.

---

## 10. Cutover Checkpoints

1. **Phase readiness gate**: contracts, schemas, dashboards, rollback drills done.
2. **Shadow-read pass**: parity >= 99.9% across representative traffic.
3. **Canary pass**: service handles canary traffic within SLO.
4. **Write cutover pass**: single-writer switch validated.
5. **Stabilization pass**: 7-day error/latency/event-lag SLO compliance.
6. **Legacy demotion pass**: monolith path moved to adapter/read-only.

---

## 11. Extraction Steps (Per Service)

### Phase A

#### Step A1
- Source monolith modules: sessions/login, password reset, token issuance, auth middleware.
- Target service: `auth_service`.
- Data moved: credentials metadata, auth sessions, token revocation records.
- APIs introduced: `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/introspect`.
- Events introduced: `auth.login_succeeded`, `auth.login_failed`, `auth.token_revoked`.
- Temporary compatibility layer: gateway keeps legacy `/login` and proxies to auth service with legacy response shape.
- Rollback path: route auth endpoints back to monolith auth controllers.
- Completion criteria: 100% auth traffic routed via service with no increase in login failure rate.

#### Step A2
- Source monolith modules: user profile CRUD, user lifecycle state handling.
- Target service: `user_service`.
- Data moved: `User` profile records and lifecycle audit trail.
- APIs introduced: `/users`, `/users/{id}`, `/users/{id}/status`, `/users/{id}/preferences`.
- Events introduced: `user.created`, `user.updated`, `user.status_changed`.
- Temporary compatibility layer: legacy `/users` endpoints transformed to/from service schema.
- Rollback path: switch gateway writes to monolith and continue CDC toward service.
- Completion criteria: user CRUD parity + lifecycle transitions match monolith behavior.

#### Step A3
- Source monolith modules: role tables, permission checks, policy combinators.
- Target service: `rbac_service`.
- Data moved: roles, permissions, role_bindings, policy rules.
- APIs introduced: `/rbac/roles`, `/rbac/bindings`, `/rbac/authorize`.
- Events introduced: `rbac.role_assigned`, `rbac.role_revoked`, `rbac.policy_updated`.
- Temporary compatibility layer: monolith authorization hooks call `rbac_service` via sidecar adapter.
- Rollback path: fallback to monolith in-process policy evaluation.
- Completion criteria: authorization decisions match baseline with zero critical access regressions.

### Phase B

#### Step B1
- Source monolith modules: account scoping, tenant key derivation, tenant settings.
- Target service: `tenant_service`.
- Data moved: tenant registry, tenant settings, tenant status.
- APIs introduced: `/tenants`, `/tenants/{id}`, `/tenants/{id}/settings`.
- Events introduced: `tenant.created`, `tenant.updated`, `tenant.status_changed`.
- Temporary compatibility layer: gateway injects tenant context resolved by `tenant_service`.
- Rollback path: use monolith tenant resolution middleware.
- Completion criteria: all requests consistently resolve tenant context from service.

#### Step B2
- Source monolith modules: institution metadata, institution-admin mappings.
- Target service: `institution_service`.
- Data moved: institution records, institution membership/admin links.
- APIs introduced: `/institutions`, `/institutions/{id}`, `/institutions/{id}/members`.
- Events introduced: `institution.created`, `institution.updated`, `institution.member_linked`.
- Temporary compatibility layer: monolith org pages read institution data through adapter.
- Rollback path: revert reads/writes to monolith institution tables.
- Completion criteria: institution CRUD and membership flows fully served by service.

### Phase C

#### Step C1
- Source monolith modules: course catalog, course lifecycle and publication workflows.
- Target service: `course_service`.
- Data moved: `Course` records, course metadata, publication states.
- APIs introduced: `/courses`, `/courses/{id}`, `/courses/{id}/publish`.
- Events introduced: `course.created`, `course.updated`, `course.published`.
- Temporary compatibility layer: legacy catalog endpoints proxy to service; response adapter preserves old fields.
- Rollback path: route course write/read traffic to monolith, replay buffered service events.
- Completion criteria: course create/update/publish parity and catalog read SLO met.

#### Step C2
- Source monolith modules: lesson authoring, lesson ordering, lesson publication.
- Target service: `lesson_service`.
- Data moved: `Lesson` records, sequencing metadata.
- APIs introduced: `/lessons`, `/lessons/{id}`, `/courses/{id}/lessons/reorder`.
- Events introduced: `lesson.created`, `lesson.updated`, `lesson.published`.
- Temporary compatibility layer: course detail view hydrates lesson data from service adapter.
- Rollback path: return lesson CRUD to monolith lesson modules.
- Completion criteria: lesson CRUD + ordering behavior unchanged for existing clients.

#### Step C3
- Source monolith modules: enrollment creation, status transitions, unenroll/withdraw logic.
- Target service: `enrollment_service`.
- Data moved: `Enrollment` records and status history.
- APIs introduced: `/enrollments`, `/enrollments/{id}`, `/enrollments/{id}/status`.
- Events introduced: `enrollment.created`, `enrollment.status_changed`.
- Temporary compatibility layer: enrollment endpoints in monolith proxy to service.
- Rollback path: switch back to monolith enrollment writes and pause service-owned transitions.
- Completion criteria: enrollment lifecycle transitions preserve all existing edge-case behavior.

#### Step C4
- Source monolith modules: progress tracking updates and completion calculations.
- Target service: `progress_service`.
- Data moved: `Progress` records, progress activity timestamps, completion states.
- APIs introduced: `/progress`, `/progress/{id}`, `/enrollments/{id}/progress`.
- Events introduced: `progress.updated`, `progress.completed`.
- Temporary compatibility layer: SCORM/xAPI processors keep legacy endpoints but forward writes to service.
- Rollback path: re-enable monolith progress writers; rebuild service state via replay.
- Completion criteria: progress accuracy parity and completion status integrity validated.

#### Step C5
- Source monolith modules: certificate issuance and verification endpoints.
- Target service: `certificate_service`.
- Data moved: `Certificate` records, verification metadata, revocation status.
- APIs introduced: `/certificates`, `/certificates/{id}`, `/certificates/verify/{code}`.
- Events introduced: `certificate.issued`, `certificate.revoked`.
- Temporary compatibility layer: certificate download links remain stable, backed by service.
- Rollback path: route issuance and verification back to monolith certificate module.
- Completion criteria: certificate issue/verify/revoke flows remain backward compatible.

### Phase D

#### Step D1
- Source monolith modules: learning path/program grouping.
- Target service: `program_service`.
- Data moved: program definitions, program-course mappings.
- APIs introduced: `/programs`, `/programs/{id}`, `/programs/{id}/courses`.
- Events introduced: `program.created`, `program.updated`, `program.courses_mapped`.
- Temporary compatibility layer: monolith learning path pages consume service APIs.
- Rollback path: revert program operations to monolith.
- Completion criteria: programs manage cross-course paths without affecting course ownership.

#### Step D2
- Source monolith modules: cohort creation and roster assignment.
- Target service: `cohort_service`.
- Data moved: cohort records, cohort memberships.
- APIs introduced: `/cohorts`, `/cohorts/{id}`, `/cohorts/{id}/members`.
- Events introduced: `cohort.created`, `cohort.member_added`, `cohort.member_removed`.
- Temporary compatibility layer: bulk assignment jobs call service with legacy payload mapping.
- Rollback path: restore monolith cohort roster writes.
- Completion criteria: cohort lifecycle and membership scale targets met.

#### Step D3
- Source monolith modules: class/session scheduler and attendance logs.
- Target service: `session_service`.
- Data moved: session schedules, attendance records.
- APIs introduced: `/sessions`, `/sessions/{id}`, `/sessions/{id}/attendance`.
- Events introduced: `session.created`, `session.updated`, `session.attendance_marked`.
- Temporary compatibility layer: calendar UI continues using legacy endpoint facade.
- Rollback path: switch scheduling back to monolith scheduler.
- Completion criteria: session scheduling and attendance remain intact for instructors.

#### Step D4
- Source monolith modules: quiz/test authoring and grading.
- Target service: `assessment_service`.
- Data moved: assessments, attempts, scores.
- APIs introduced: `/assessments`, `/assessments/{id}/attempts`, `/attempts/{id}/submit`.
- Events introduced: `assessment.created`, `assessment.attempt_submitted`, `assessment.graded`.
- Temporary compatibility layer: gradebook reads aggregate from assessment service via adapter.
- Rollback path: restore monolith assessment execution paths.
- Completion criteria: attempt/grade integrity and gradebook parity validated.

### Phase E

#### Step E1
- Source monolith modules: existing webhook/event hooks and ETL scripts.
- Target service: `event_ingestion_service`.
- Data moved: event registry metadata and ingestion configs.
- APIs introduced: `/events/ingest`, `/events/schema`, `/events/replay`.
- Events introduced: normalized canonical domain events for all runtime entities.
- Temporary compatibility layer: monolith continues publishing legacy events mirrored into ingestion service.
- Rollback path: bypass ingestion service and publish directly from existing pipelines.
- Completion criteria: no event loss, schema validation and replay tooling operational.

#### Step E2
- Source monolith modules: reporting jobs and analytical materialized views.
- Target service: `learning_analytics_service`.
- Data moved: analytical projections only (not operational SoT records).
- APIs introduced: `/analytics/learner`, `/analytics/course`, `/analytics/institution`.
- Events introduced: `analytics.snapshot_built`, `analytics.metric_computed`.
- Temporary compatibility layer: legacy reports query analytics service through report adapter.
- Rollback path: switch reports back to monolith analytical jobs.
- Completion criteria: analytics parity with accepted tolerance and no runtime write coupling.

### Phase F

#### Step F1
- Source monolith modules: tutoring assistants and guidance widgets (if any).
- Target service: `ai_tutor_service`.
- Data moved: tutor session transcripts/prompts (extension data only).
- APIs introduced: `/ai/tutor/sessions`, `/ai/tutor/respond`.
- Events introduced: `ai_tutor.response_generated`, `ai_tutor.feedback_received`.
- Temporary compatibility layer: UI widget calls gateway; fallback to static guidance if unavailable.
- Rollback path: disable AI route, preserve core learning flows unaffected.
- Completion criteria: no impact to core runtime when AI service degraded.

#### Step F2
- Source monolith modules: recommendation widgets/rules.
- Target service: `recommendation_service`.
- Data moved: recommendation models/features/projections (non-authoritative).
- APIs introduced: `/ai/recommendations/users/{id}`, `/ai/recommendations/courses/{id}`.
- Events introduced: `recommendation.generated`, `recommendation.clicked`.
- Temporary compatibility layer: fallback to deterministic rules in monolith if service unavailable.
- Rollback path: disable service and route to legacy rules engine.
- Completion criteria: recommendations are additive; zero coupling to enrollment/progress writes.

#### Step F3
- Source monolith modules: skill tagging/inference jobs.
- Target service: `skill_inference_service`.
- Data moved: inferred skill profiles and confidence scores.
- APIs introduced: `/ai/skills/users/{id}`, `/ai/skills/infer`.
- Events introduced: `skill_inference.updated`, `skill_gap.detected`.
- Temporary compatibility layer: UI consumes optional skill panels; hidden via flag if unavailable.
- Rollback path: disable inference service without affecting completion/progress flows.
- Completion criteria: inferred skills remain extension-only and non-blocking.

---

## 12. Monolith Compatibility Layer (Detailed)

### 12.1 Request routing rules

1. Default route to monolith unless capability is marked `service_active`.
2. Reads transition first (shadow -> canary -> full).
3. Writes switch only after data parity and rollback checkpoint completion.
4. Emergency kill-switch routes all capabilities to monolith-safe paths where possible.

### 12.2 Dual-write avoidance rules

- Exactly one authoritative writer per entity at any time.
- During migration, use CDC/outbox replication; never parallel business writes from both systems.
- For temporary mirrors, mark one side strictly read-only.

### 12.3 Event backfill strategy

- Backfill from monolith snapshots + historical change logs.
- Emit synthetic historical events with `backfill=true` metadata and original timestamps.
- Process backfill in deterministic windows (by tenant and date range), then switch to live stream.

### 12.4 Data sync strategy

- Snapshot load -> CDC tailing -> lag drain -> cutover.
- Data parity checks by counts, checksums, and semantic invariants (e.g., completion counts by course).
- Continuous drift detection alerts post-cutover for two release cycles.

### 12.5 Schema migration checkpoints

- C0: add non-breaking columns/tables in monolith (if needed).
- C1: deploy service schemas and constraints.
- C2: complete backfill and consistency checks.
- C3: enable service writes.
- C4: set monolith moved-domain tables read-only.
- C5: archive/decommission legacy schema (deferred).

---

## 13. QC LOOP

### QC Round 1 (Initial Assessment)

| Category | Score | Flaw Identified |
|---|---:|---|
| migration safety | 9 | Lacked explicit write-freeze guard during ownership switch. |
| repo alignment | 10 | None. |
| service extraction order | 10 | None. |
| boundary correctness | 9 | Needed stricter rule preventing extracted services from synchronous monolith write dependencies. |
| rollback safety | 9 | Needed rollback SLA targets and explicit route-vs-data rollback levels. |
| backward compatibility | 10 | None. |
| operational realism | 9 | Needed concrete SLO gates and stabilization windows. |
| anti-spaghetti quality | 9 | Needed acyclic dependency policy and direction constraints. |
| tenant-readiness | 10 | None. |
| future AI-readiness | 10 | None. |

Corrections applied:
1. Added single-writer ownership states + bounded freeze requirement.
2. Added anti-circular synchronous-call prohibition.
3. Added rollback levels with SLA targets.
4. Added explicit cutover gates and 7-day stabilization checkpoint.
5. Added dependency direction policy across phases.

### QC Round 2 (Post-Correction)

| Category | Score |
|---|---:|
| migration safety | 10 |
| repo alignment | 10 |
| service extraction order | 10 |
| boundary correctness | 10 |
| rollback safety | 10 |
| backward compatibility | 10 |
| operational realism | 10 |
| anti-spaghetti quality | 10 |
| tenant-readiness | 10 |
| future AI-readiness | 10 |

QC exit condition satisfied: all categories are 10/10.
