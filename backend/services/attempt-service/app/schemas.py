from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    SCORED = "scored"


class AnswerSubmission(BaseModel):
    question_id: str
    response: str | list[str] | dict[str, str | int | float | bool | None]
    is_final: bool = True


class StartAttemptRequest(BaseModel):
    tenant_id: str
    learner_id: str
    assessment_id: str
    enrollment_id: str | None = None
    course_id: str | None = None
    started_by: str


class RecordAnswersRequest(BaseModel):
    tenant_id: str
    answers: list[AnswerSubmission] = Field(default_factory=list)


class ScoreAttemptRequest(BaseModel):
    tenant_id: str
    scored_by: str
    max_score: float = Field(gt=0)
    awarded_score: float = Field(ge=0)
    passing_score: float = Field(ge=0)
    feedback: str | None = None


class AttemptAnswerResponse(BaseModel):
    question_id: str
    response: str | list[str] | dict[str, str | int | float | bool | None]
    is_final: bool
    updated_at: datetime


class AttemptResponse(BaseModel):
    attempt_id: str
    tenant_id: str
    learner_id: str
    assessment_id: str
    enrollment_id: str | None = None
    course_id: str | None = None
    attempt_number: int
    status: AttemptStatus
    started_by: str
    started_at: datetime
    submitted_at: datetime | None = None
    scored_at: datetime | None = None
    scored_by: str | None = None
    answers: list[AttemptAnswerResponse] = Field(default_factory=list)
    max_score: float | None = None
    awarded_score: float | None = None
    passing_score: float | None = None
    passed: bool | None = None
    feedback: str | None = None


class AttemptHistoryResponse(BaseModel):
    tenant_id: str
    learner_id: str
    assessment_id: str | None = None
    attempts: list[AttemptResponse] = Field(default_factory=list)
