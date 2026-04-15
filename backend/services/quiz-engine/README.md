# Quiz Engine Service

Lightweight in-memory quiz engine for LMS assessments.

## Features

- Quiz rendering payload generation (without answer key leakage)
- Seeded question randomization per session
- Session timer and expiration handling
- Deterministic scoring engine with pass/fail threshold

## Structure

- `src/models.py`: domain models for quiz definitions, sessions, and scores
- `src/quiz_engine.py`: orchestration logic for session lifecycle and scoring
- `tests/test_quiz_engine.py`: coverage for rendering, randomization, timer, and scoring

## Run tests

```bash
cd backend/services/quiz-engine
pytest -q
```
