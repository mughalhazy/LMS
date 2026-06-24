# Attempt Service — Spec

**Service:** `attempt-service` | **Gateway:** `/api/v1/attempt`, `/api/v1/attempts` | **Port:** varies

## Purpose

Manages learner assessment attempt lifecycle — from session start through answer recording to scoring and pass/fail determination. Tenant-scoped with per-learner attempt numbering.

## Responsibilities

- Attempt lifecycle: start → answers recorded → submitted → scored
- Per-learner attempt numbering per assessment (attempt_number auto-incremented)
- Answer upsert with finality flag
- Scoring: awarded_score vs passing_score, pass/fail computation
- Audit logging of all submission events
- Event emission on assessment failure (BC-WF-01)

## Out of scope

- Question content management (owned by `assessment-service`)
- Certification issuance on pass (owned by `certificate-service`)
- Progress tracking updates (owned by `progress-service`)

## Data model

| Entity | Fields |
|---|---|
| `AttemptRecord` | attempt_id, tenant_id, learner_id, assessment_id, enrollment_id, course_id, attempt_number, status, started_by, started_at, submitted_at, scored_at, scored_by, answers{}, max_score, awarded_score, passing_score, passed, feedback |
| `AttemptAnswerRecord` | question_id, response, is_final, updated_at |

## Status lifecycle

`IN_PROGRESS → SUBMITTED → SCORED`

Scored attempts are immutable — answer recording rejected after scoring.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/attempts` | Start new attempt |
| POST | `/api/v1/attempts/{attemptId}/answers` | Record/upsert answers |
| POST | `/api/v1/attempts/{attemptId}/score` | Score attempt |
| GET | `/api/v1/attempts/{attemptId}` | Get attempt |
| GET | `/api/v1/attempts/history` | Learner attempt history, filterable by assessment |

## Behavioral rules

- awarded_score cannot exceed max_score; passing_score cannot exceed max_score
- Attempt number increments per (tenant_id, learner_id, assessment_id) tuple
- Answers keyed by question_id; upsert semantics (last write wins per question)
- On scoring failure (passed=False): emits `assessment.failed` event via shared event bus (CGAP-067 / BC-WF-01)
- Event emission failure does not fail the scoring operation

## Events emitted

| Event | Trigger |
|---|---|
| `assessment.failed` | Score recorded and passed=False |

## Integration

- Produces: `assessment.failed` → shared event bus → workflow-engine
- Consumed by: `workflow-engine` (for remediation flow triggers)
- Audit log: structured entries per submission event
