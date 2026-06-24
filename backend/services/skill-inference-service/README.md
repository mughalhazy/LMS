# Skill Inference Service

Tenant-scoped service for:
- inferring learner skills from evidence streams,
- updating learner skill levels,
- generating mastery predictions,
- and updating/propagating skill graph relationships.

## Core capabilities

1. **Infer learner skills** from weighted evidence (`assessment`, `quiz`, `project`, `course_completion`).
2. **Update skill levels** on the 0-5 scale with confidence and evidence counts.
3. **Mastery predictions** via a composite score and mastery bands (`novice`, `developing`, `proficient`, `expert`).
4. **Skill graph updates** for `PREREQUISITE_OF` and `RELATED_TO` relationships.

## API routes

Authentication: JWT required (`Authorization: Bearer <token>`). Added 2026-06-01 (B13-001).

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/analytics/ingest` | Ingest analytics signals (assessment, quiz, course_completion evidence) |
| POST | `/api/v1/knowledge-graph/upsert` | Upsert skill graph nodes and edges |
| POST | `/api/v1/inference/run` | Run skill inference for a learner — returns inferred skills + mastery + explainability |
| GET | `/api/v1/learners/{tenant_id}/{learner_id}/progression` | Get learner skill progression state |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Structure

- `app/main.py`: FastAPI entrypoint with JWT auth.
- `app/service.py`: `SkillInferenceApplicationService` — orchestration layer.
- `src/entities.py`: domain models (`SkillNode`, `LearnerSkillState`, `LearnerSkillEvidence`, etc.)
- `src/skill_inference_service.py`: inference engine + graph propagation logic
- `tests/test_skill_inference_service.py`: behavior tests

## Design reference

`docs/specs/skill-inference-service-spec.md`

## Run tests

```bash
python -m unittest backend/services/skill-inference-service/tests/test_skill_inference_service.py
```
