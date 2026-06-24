# Quiz Engine Service

FastAPI microservice for formative in-course quiz delivery. Distinct from exam-engine (which handles proctored high-stakes assessments).

## Features

- Quiz rendering without answer-key leakage
- Seeded question randomisation per session
- Session timer and expiration handling
- Deterministic scoring with configurable pass/fail threshold

## REST API

Spec: `Repo/docs/specs/quiz-engine-spec.md`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/quizzes` | Register a quiz definition |
| `POST` | `/api/v1/quizzes/{quiz_id}/sessions` | Start a quiz session |
| `GET` | `/api/v1/sessions/{session_id}` | Render quiz (questions without answer key) |
| `POST` | `/api/v1/sessions/{session_id}/answers` | Submit an answer for one question |
| `POST` | `/api/v1/sessions/{session_id}:submit` | Submit the quiz and return score |
| `GET` | `/api/v1/sessions/{session_id}/score` | Retrieve score for a submitted session |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Service metrics |

Tenant context via `X-Tenant-Id` header.

## Structure

- `src/models.py`: domain models — `QuizDefinition`, `QuizQuestion`, `QuizOption`, `QuizSession`, `QuizScore`
- `src/quiz_engine.py`: session lifecycle and scoring engine
- `app/schemas.py`: Pydantic request schemas — `RegisterQuizRequest`, `StartSessionRequest`, `SubmitAnswerRequest`, `SubmitQuizRequest`
- `app/service.py`: thin alias extending `QuizEngine`
- `app/main.py`: FastAPI app with all routes
- `tests/test_quiz_engine.py`: rendering, randomisation, timer, and scoring coverage

## Run

```bash
cd backend/services/quiz-engine
uvicorn app.main:app --port 8090
```

## Run tests

```bash
cd backend/services/quiz-engine
pytest -q
```
