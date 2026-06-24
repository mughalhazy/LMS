# Skill Analytics Service

Implements tenant-scoped analytics across three spec-defined metrics per `docs/specs/features/skill-analytics-spec.md`.

Authentication: JWT required (`Authorization: Bearer <token>`).

## API routes

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/skill-analytics/learners/{learner_id}/progress` | Skill Progress — baseline, absolute change, velocity, milestone attainment (query: tenant_id, skill_id, target_level, time_window_days) |
| POST | `/api/v1/skill-analytics/learners/{learner_id}/gaps` | Skill Gap Detection — ranked gap list with severity + recommended interventions (body: tenant_id, role_profile_id, urgency_factor) |
| GET | `/api/v1/skill-analytics/learners/{learner_id}/mastery/{skill_id}` | Skill Mastery Score — composite score + mastery band (novice/developing/proficient/expert) (query: tenant_id) |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

Routes added 2026-06-01 (B13-003). JWT added 2026-06-01 (B13-002).

## Core entities used
- `Skill`
- `UserSkill`
- `UserSkillEvidence`
- `RoleSkillRequirement`

## Design reference

`docs/specs/features/skill-analytics-spec.md`

## Running tests

```bash
python -m unittest backend/services/skill-analytics-service/tests/test_skill_analytics_service.py
```
