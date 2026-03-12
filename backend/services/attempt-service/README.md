# Attempt Service

Tenant-scoped service for managing learner assessment attempts, including answer storage, scoring results, and attempt history.

## Capabilities
- Start learner attempts with per-learner attempt sequencing.
- Store and update per-question answers on an attempt.
- Record scoring outcomes (max score, awarded score, passing score, pass/fail, feedback).
- Return learner attempt history filtered by assessment.

## Endpoints
- `POST /attempts`
- `POST /attempts/{attempt_id}/answers`
- `POST /attempts/{attempt_id}/score`
- `GET /attempts/{attempt_id}?tenant_id=...`
- `GET /attempts/history?tenant_id=...&learner_id=...&assessment_id=...`

## Local test
```bash
pytest backend/services/attempt-service/tests/test_attempt_service.py
```
