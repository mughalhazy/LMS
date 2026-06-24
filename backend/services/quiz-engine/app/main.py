"""Service entrypoint — quiz-engine REST API."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import Response

from src.models import QuizDefinition, QuizOption, QuizQuestion, QuestionType
from src.quiz_engine import NotFoundError, SessionExpiredError, ValidationError
from .service import Service
from .schemas import (
    RegisterQuizRequest,
    StartSessionRequest,
    SubmitAnswerRequest,
    SubmitQuizRequest,
)
from .security import apply_security_headers, require_jwt

# B03-001: multi-tenant-isolation-model §2 — JWT required on all routes
app = FastAPI(title="quiz-engine", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

apply_security_headers(app)
_ENGINE = Service()


def _tenant_context(
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id, x_actor_id or "system"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "quiz-engine"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "quiz-engine", "service_up": 1, "active_sessions": len(_ENGINE._sessions)}


@app.post("/api/v1/quiz-engine/quizzes", status_code=status.HTTP_201_CREATED)
def register_quiz(
    request: RegisterQuizRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    # Build typed domain objects from the incoming Pydantic model
    tenant_id, _ = ctx
    try:
        questions = [
            QuizQuestion(
                question_id=q.question_id,
                prompt=q.prompt,
                question_type=QuestionType(q.question_type),
                options=[
                    QuizOption(option_id=o.option_id, text=o.text, is_correct=o.is_correct)
                    for o in q.options
                ],
                points=q.points,
            )
            for q in request.questions
        ]
        quiz = QuizDefinition(
            quiz_id=request.quiz_id,
            tenant_id=tenant_id,
            title=request.title,
            questions=questions,
            duration_seconds=request.duration_seconds,
            randomize_questions=request.randomize_questions,
        )
        _ENGINE.register_quiz(quiz)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "quiz_id": quiz.quiz_id,
        "tenant_id": tenant_id,
        "title": quiz.title,
        "question_count": len(questions),
        "duration_seconds": quiz.duration_seconds,
    }


@app.post("/api/v1/quiz-engine/quizzes/{quiz_id}/sessions", status_code=status.HTTP_201_CREATED)
def start_session(
    quiz_id: str,
    request: StartSessionRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        session = _ENGINE.start_session(
            tenant_id=tenant_id,
            quiz_id=quiz_id,
            user_id=request.user_id,
            seed=request.seed,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "session_id": session.session_id,
        "quiz_id": session.quiz_id,
        "user_id": session.user_id,
        "started_at": session.started_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "question_count": len(session.ordered_question_ids),
    }


@app.get("/api/v1/quiz-engine/sessions/{session_id}")
def render_quiz(session_id: str) -> dict:
    try:
        return _ENGINE.render_quiz(session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/v1/quiz-engine/sessions/{session_id}/answers", status_code=status.HTTP_204_NO_CONTENT)
def submit_answer(session_id: str, request: SubmitAnswerRequest) -> Response:
    try:
        _ENGINE.submit_answer(session_id, request.question_id, request.option_ids)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SessionExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/v1/quiz-engine/sessions/{session_id}:submit")
def submit_quiz(session_id: str, request: SubmitQuizRequest) -> dict:
    try:
        score = _ENGINE.submit_quiz(session_id, submitted_at=request.submitted_at)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return {
        "session_id": session_id,
        "score": score.score,
        "max_score": score.max_score,
        "percentage": score.percentage,
        "passed": score.passed,
        "per_question": score.per_question,
    }


@app.get("/api/v1/quiz-engine/sessions/{session_id}/score")
def get_score(session_id: str) -> dict:
    try:
        score = _ENGINE.score_session(session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "session_id": session_id,
        "score": score.score,
        "max_score": score.max_score,
        "percentage": score.percentage,
        "passed": score.passed,
        "per_question": score.per_question,
    }


# B03-002: spec §API defines POST /api/v1/quiz-engine/sessions (quiz_id in body, not path)
@app.post("/api/v1/quiz-engine/sessions", status_code=status.HTTP_201_CREATED)
def start_session_body(
    request: StartSessionRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    if not request.quiz_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="quiz_id required in body")
    tenant_id, _ = ctx
    try:
        session = _ENGINE.start_session(
            tenant_id=tenant_id,
            quiz_id=request.quiz_id,
            user_id=request.user_id,
            seed=request.seed,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "session_id": session.session_id,
        "quiz_id": session.quiz_id,
        "user_id": session.user_id,
        "started_at": session.started_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "question_count": len(session.ordered_question_ids),
    }


# B03-003: spec uses slash-style submit path /sessions/{id}/submit; code uses colon (:submit) — add alias
app.add_api_route(
    "/api/v1/quiz-engine/sessions/{session_id}/submit",
    submit_quiz,
    methods=["POST"],
)
