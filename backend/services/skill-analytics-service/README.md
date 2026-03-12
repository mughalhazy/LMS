# Skill Analytics Service

Implements tenant-scoped analytics for:
- skill progression metrics
- skill gap detection
- skill mastery scoring
- skill learning trends

## Core entities used
- `Skill`
- `UserSkill`
- `UserSkillEvidence`
- `RoleSkillRequirement`

## Running tests

```bash
python -m unittest backend/services/skill-analytics-service/tests/test_skill_analytics_service.py
```
