# AI_03_skill_inference_service — Cleaned Spec

## Inputs
- Tenant and actor context (`tenant_id`, request identity, correlation metadata).
- Learner scope (`user_id`, optional course/lesson/time-window constraints).
- Read-only upstream references:
  - learning events
  - assessment results
  - progress records
  - knowledge graph relationships
  - recommendation context signals (optional)
- Inference configuration:
  - inference version
  - idempotency key
  - explainability policy profile

## Logic
1. Validate tenancy and learner scope.
2. Collect and normalize evidence from upstream references.
3. Execute inference/scoring with deterministic idempotent behavior.
4. Build explainability payload (confidence, evidence references, version metadata).
5. Persist derived skill profile state and inference run record.
6. Emit skill inference and profile update domain events.
7. Record immutable audit trail and telemetry markers.
8. Support partial-failure handling with retry/dead-letter strategy for event publication failures.

### Guardrails
- Inferred skills are derived intelligence and never runtime completion source-of-truth.
- No ownership transfer from assessment or progress domains.
- Tenant safety is enforced across request handling, persistence, events, logs, and metrics.

## Outputs
- Skill profile response with:
  - inferred skills
  - proficiency and progression state
  - explainability evidence references
  - inference version metadata
- Inference run outcome with completion status and confidence summary.
- Domain events:
  - `lms.ai.skill_inference.completed.v1`
  - `lms.ai.skill_profile.updated.v1`
  - `lms.ai.skill_gap.detected.v1` (conditional)
- Audit and observability outputs with trace/correlation linkage.

## QC + Auto-Fix
- Broken-reference check: passed (no stale path references).
- Boundary check: passed (derived-data-only ownership retained).
- Idempotency check: passed (repeat-input handling preserved).
- Logic integrity check: passed (inference flow complete and unchanged in intent).

**Score: 10/10**
