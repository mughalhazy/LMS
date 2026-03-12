# Course Generation Service

FastAPI microservice implementing the AI Course Generation pipeline described in `docs/architecture/ai_course_generation.md`.

## Implemented stages
- Document ingestion
- Topic extraction
- Lesson generation
- Quiz generation

## Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

## files_created
- `app/main.py`
- `app/service.py`
- `app/schemas.py`
- `tests/test_course_generation_service.py`
- `requirements.txt`

## generation_pipeline
1. Ingest source documents into normalized chunks with traceability metadata.
2. Extract ranked topics and create a prerequisite graph from ingested chunks.
3. Generate draft lessons for each extracted topic.
4. Generate quizzes mapped to generated lessons.
5. Optionally execute all stages in one call using pipeline run endpoint.

## api_endpoints
- `POST /course-generation/ingestions`
- `POST /course-generation/topics:extract`
- `POST /course-generation/lessons:generate`
- `POST /course-generation/quizzes:generate`
- `POST /course-generation/pipeline:run`
