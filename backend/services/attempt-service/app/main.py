from __future__ import annotations

from fastapi import FastAPI

from .schemas import (
    AttemptHistoryResponse,
    AttemptResponse,
    RecordAnswersRequest,
    ScoreAttemptRequest,
    StartAttemptRequest,
)
from .service import AttemptService

app = FastAPI(title="Attempt Service", version="0.1.0")
service = AttemptService()


@app.post("/attempts", response_model=AttemptResponse)
def start_attempt(request: StartAttemptRequest) -> AttemptResponse:
    return service.start_attempt(request)


@app.post("/attempts/{attempt_id}/answers", response_model=AttemptResponse)
def record_answers(attempt_id: str, request: RecordAnswersRequest) -> AttemptResponse:
    return service.record_answers(attempt_id, request)


@app.post("/attempts/{attempt_id}/score", response_model=AttemptResponse)
def score_attempt(attempt_id: str, request: ScoreAttemptRequest) -> AttemptResponse:
    return service.score_attempt(attempt_id, request)


@app.get("/attempts/{attempt_id}", response_model=AttemptResponse)
def get_attempt(attempt_id: str, tenant_id: str) -> AttemptResponse:
    return service.get_attempt(tenant_id, attempt_id)


@app.get("/attempts/history", response_model=AttemptHistoryResponse)
def get_attempt_history(
    tenant_id: str,
    learner_id: str,
    assessment_id: str | None = None,
) -> AttemptHistoryResponse:
    return service.get_attempt_history(
        tenant_id=tenant_id,
        learner_id=learner_id,
        assessment_id=assessment_id,
    )
