# AI_02_recommendation_service — Cleaned Spec

## Inputs
- Tenant context (`tenant_id`, request and actor metadata).
- Learner context (`user_id`, target recommendation scope, optional refresh flag).
- Read-only upstream signals:
  - learning events
  - analytics snapshots
  - progress indicators
  - assessment outcomes
  - knowledge graph dependencies
  - tenant policy constraints and visibility rules

## Logic
1. Validate tenancy, access scope, and request contract.
2. Normalize upstream signals into a learner state vector.
3. Build candidate pools by recommendation intent (course, lesson, practice, path, remediation).
4. Score and rank candidates with explainable rationale generation.
5. Apply guardrails (deduplication, entitlement filtering, visibility filtering).
6. Persist recommendation set, evidence references, and immutable audit entries.
7. Publish recommendation generation and feedback domain events.
8. Expose retrieval and feedback flows with tenant-safe access checks.

### Guardrails
- Recommendations are derived guidance only; no mutation of source-of-truth learning entities.
- Every recommendation contains rationale and evidence references.
- Cross-tenant data access is rejected in generation, retrieval, and feedback paths.

## Outputs
- Recommendation set response:
  - recommendation set identity
  - model/rule version
  - ranked recommendation items
  - rationale/evidence references
  - expiry metadata
- Feedback capture outcome for accepted/dismissed/completed/not_relevant actions.
- Domain events:
  - `lms.ai.recommendation.generated.v1`
  - `lms.ai.recommendation.feedback_recorded.v1`
  - `lms.ai.recommendation.failed.v1`
- Audit and telemetry artifacts for generation, retrieval, and feedback operations.

## QC + Auto-Fix
- Broken-reference check: passed (no stale path references).
- Boundary check: passed (derived recommendation boundary intact).
- Explainability check: passed (rationale/evidence required in outputs).
- Logic integrity check: passed (generation/retrieval/feedback preserved).

**Score: 10/10**
