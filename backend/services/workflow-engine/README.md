# workflow-engine

Event-driven automation backbone. Executes pre-configured multi-step workflows in response to domain events without code changes. Ships 6 default-on workflow templates per BC-WF-01. Spec: `docs/specs/workflow-engine-spec.md` (MS§5.8).

## Default-on automations (BC-WF-01)
enrollment.completed | assessment.failed | learner.inactivity_threshold_crossed | fee.overdue_threshold_crossed | student.absence_threshold_crossed | batch.capacity_below_threshold

## Gateway
Route: `/api/v1/workflow` | Rate limit: `internal-control-plane`
