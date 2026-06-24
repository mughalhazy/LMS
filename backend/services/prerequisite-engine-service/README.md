# Prerequisite Engine Service

Tenant-scoped **Python/FastAPI** service enforcing course prerequisites and learning-path dependency rules per `docs/specs/features/prerequisite-engine-spec.md`.

Authentication: JWT required (`Authorization: Bearer <token>`).

## API routes

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/prerequisites/enroll` | Evaluate enrollment eligibility — returns APPROVED or BLOCKED with unmet prerequisites + remedial recommendations |
| POST | `/api/v1/prerequisites/enroll/override` | Instructor/admin override — allows enrollment regardless of prerequisite state; audit-logged with reason code |
| POST | `/api/v1/prerequisites/path-progression` | Recompute learning-path node unlock state after an attempt outcome |
| POST | `/api/v1/prerequisites/eligibility` | Batch eligibility check across multiple courses for a learner |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

Routes and JWT added 2026-06-01 (B13-005/006).

## Responsibilities
- Manage course prerequisite rule definitions per tenant.
- Evaluate prerequisites against learner transcript (completion status, grade threshold, validity window, equivalency mappings).
- Recompute learning-path dependency DAG unlock states on each progression event.
- Support policy override with full audit trail (instructor/admin reason code required).

## Key modules
- `app/service.py` — `PrerequisiteEngineService` — facade over validators
- `app/course_prerequisite_validator.py` — validates transcript against prerequisite rules
- `app/learning_path_progression_validator.py` — recomputes DAG node unlock states
- `app/learner_eligibility_validator.py` — cross-course eligibility checks

## Run
```bash
uvicorn app.main:app --reload --port 8101
```

## Tests
```bash
python -m pytest backend/services/prerequisite-engine-service/tests/ -q
```
