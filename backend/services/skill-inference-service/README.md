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

## Structure

- `src/entities.py`: domain models (`SkillNode`, `LearnerSkillState`, `LearnerSkillEvidence`, etc.)
- `src/skill_inference_service.py`: inference engine + graph propagation logic
- `tests/test_skill_inference_service.py`: behavior tests

## Run tests

```bash
python -m unittest backend/services/skill-inference-service/tests/test_skill_inference_service.py
```
