# AI Tutor Service

AI Tutor Service provides learner-facing tutoring capabilities for LMS:

- AI concept explanation
- learner Q&A assistant
- contextual tutoring
- learning guidance

## API Endpoints

- `POST /ai-tutor/explanations` — Generate concept explanations tailored to learner context.
- `POST /ai-tutor/questions` — Return guided answers to learner questions.
- `POST /ai-tutor/contextual-tutoring` — Provide feedback for submissions against expected outcomes.
- `POST /ai-tutor/guidance` — Produce adaptive study guidance using progress and available study time.
- `GET /ai-tutor/sessions/{session_id}?tenant_id=...` — Retrieve tenant-scoped tutoring session history.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```
