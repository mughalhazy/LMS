# Recommendation Service

Generates adaptive recommendations for learners across four domains:

- Personalized course recommendations.
- Skill gap recommendations.
- Learning path suggestions.
- Behavioral learning recommendations.

## API Endpoints

- `POST /recommendations/personalized-courses`
- `POST /recommendations/skill-gaps`
- `POST /recommendations/learning-paths`
- `POST /recommendations/behavioral`
- `GET /learners/{learner_id}/recommendations?tenant_id={tenant_id}`

## Local test

```bash
cd backend/services/recommendation-service
PYTHONPATH=. pytest -q
```
