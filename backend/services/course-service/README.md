# Course Service

FastAPI microservice implementing tenant-scoped course catalog operations.

## Implemented capabilities
- Course creation (`POST /courses`)
- Course metadata updates (`PATCH /courses/{course_id}`)
- Course publishing workflow (`POST /courses/{course_id}/publish`)
- Course version management (`POST /courses/{course_id}/versions`)
- Tenant-scoped retrieval and listing (`GET /courses`, `GET /courses/{course_id}`)

## Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```
