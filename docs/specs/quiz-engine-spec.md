# Quiz Engine — Spec

**Service:** `quiz-engine` | **Gateway:** `/api/v1/quiz-engine` | **Port:** varies

## Purpose

In-process quiz delivery engine for formative, in-course assessments. Handles quiz registration, session management, question rendering, timed answer submission, and deterministic scoring. Distinct from `exam-engine` (summative, high-stakes, proctored).

## Responsibilities

- Quiz definition registration (questions, options, duration, randomization)
- Session start with optional seed for deterministic question ordering
- Question rendering — strips correct-answer flags from client-facing output
- Per-question answer submission with expiry enforcement
- Quiz submission and auto-scoring (configurable pass threshold, default 70%)

## Out of scope

- Formal examination with proctoring (owned by `exam-engine` — separate service)
- Attempt persistence across restarts (in-memory; durable storage is an infrastructure concern)
- Certificate or badge issuance on pass (owned by `certificate-service`, `badge-service`)

## Data model

| Entity | Fields |
|---|---|
| `QuizDefinition` | quiz_id, tenant_id, title, questions[], duration_seconds, randomize_questions |
| `QuizQuestion` | question_id, prompt, question_type, points, options[] |
| `QuizOption` | option_id, text, is_correct |
| `QuizSession` | session_id, quiz_id, tenant_id, user_id, ordered_question_ids[], started_at, expires_at, submitted_at, answers{} |
| `QuizScore` | score, max_score, percentage, passed, per_question{} |

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/quiz-engine/quizzes` | Register quiz definition |
| POST | `/api/v1/quiz-engine/sessions` | Start quiz session |
| GET | `/api/v1/quiz-engine/sessions/{sessionId}` | Render quiz (questions without correct answers) |
| POST | `/api/v1/quiz-engine/sessions/{sessionId}/answers` | Submit answer for a question |
| POST | `/api/v1/quiz-engine/sessions/{sessionId}/submit` | Submit quiz and receive score |

## Behavioral rules

- Quiz must have at least one question and positive duration to register
- Question order is shuffled per-session when `randomize_questions=True`; seed parameter makes shuffle deterministic (reproducible for debugging/replay)
- Correct-answer flags are never returned in render output
- Answers are normalised (sorted, deduplicated) before scoring for determinism
- Answer submission rejected after session is submitted or timer expired
- Score: per-question full-credit or zero (no partial credit); percentage = earned/total × 100
- Pass threshold: configurable at engine init (default 70%)
- Session expiry is enforced at answer-submission time, not at render time

## Distinction from exam-engine

| Dimension | quiz-engine | exam-engine (separate service) |
|---|---|---|
| Stakes | Formative, in-course | Summative, high-stakes |
| Proctoring | None | Proctoring hooks |
| Compliance | None | Audit trail, compliance logging |
| Attempt limits | Unlimited | Governed by policy |
| Certificate gating | No | Yes |
