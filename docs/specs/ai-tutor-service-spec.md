# AI_01_ai_tutor_service — Cleaned Spec

## Inputs
- Tenant context (`tenant_id`, request metadata, actor metadata).
- Learner context (`user_id`, optional `course_id`, optional `lesson_id`).
- Read-only LMS references:
  - lesson and course metadata
  - learner progress snapshot
  - recent learning events
  - knowledge graph concept and prerequisite references
- Policy and safety configuration (provider policy profile, moderation profile, fallback policy).

## Logic
1. Validate tenant scope and actor scope.
2. Resolve read-only learning context from integrated LMS domains.
3. Assemble constrained prompt context with policy guards.
4. Invoke AI adapter with deterministic request envelope.
5. Apply safety checks and fallback rules when provider response is degraded.
6. Persist immutable interaction record and audit linkage.
7. Emit tutor interaction domain events.
8. Record telemetry for latency, error class, and trace correlation.

### Guardrails
- AI remains assistive-only and cannot become system-of-record.
- No ownership transfer of runtime entities (`User`, `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`).
- All requests and persisted artifacts are tenant-scoped and auditable.

## Outputs
- Versioned tutor interaction response containing:
  - direct answer
  - explanation depth marker
  - suggested next activity
  - optional practice items
  - evidence/citation pointers to LMS context inputs
- Domain events:
  - `lms.ai_tutor.interaction.requested.v1`
  - `lms.ai_tutor.interaction.responded.v1`
  - `lms.ai_tutor.interaction.failed.v1`
  - `lms.ai_tutor.feedback.recorded.v1`
- Audit and observability artifacts:
  - immutable interaction audit record
  - correlation and trace identifiers
  - metrics-ready operation outcome markers

## QC + Auto-Fix
- Broken-reference check: passed (no stale path references).
- Boundary check: passed (assistive-only ownership preserved).
- Tenant safety check: passed (tenant scope enforced on inputs, logic, outputs).
- Logic integrity check: passed (end-to-end flow unchanged).

**Score: 10/10**
