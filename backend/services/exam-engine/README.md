# exam-engine

Secure high-stakes exam delivery. Manages timed exam sessions with configurable proctoring controls (single-window, copy-paste disable, tab-switch limit, IP allowlist), attempt lifecycle, and proctor event recording. Distinct from quiz-engine (formative). Spec: `docs/specs/exam-engine-spec.md` (MS§5.1).

**Runtime:** `http.server`-based (not FastAPI). JWT validated inline via `_jwt_valid()` in `app/main.py` (B03-004, 2026-05-31).

## API routes (port 8110)

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/exam/exams` | Register exam definition with proctoring config |
| POST | `/api/v1/exam/sessions` | Start exam session — emits `exam.attempt_started` |
| GET | `/api/v1/exam/sessions/{session_id}` | Get session state; auto-marks timed_out if expired |
| POST | `/api/v1/exam/sessions/{session_id}/answers` | Record answer for a question |
| POST | `/api/v1/exam/sessions/{session_id}/submit` | Submit exam — emits `exam.submitted` |
| POST | `/api/v1/exam/sessions/{session_id}/proctor-events` | Record proctoring integrity event |
| GET | `/health` | Health check (JWT exempt) |

Authentication: `Authorization: Bearer <token>` required on all routes except `/health`. Uses `JWT_SHARED_SECRET` env var.

## Events emitted (B03-005, 2026-05-31)

- `exam.attempt_started` — published on session creation via shared event bus
- `exam.submitted` — published on exam submission
- `exam.timed_out` — published when session expiry is detected

## Design reference

`docs/specs/exam-engine-spec.md`
